from datetime import datetime

import stripe
from flask import Blueprint, render_template, request, current_app, jsonify

from app import db
from app.models import Booking, BookingStatus, Ticket
from app.services.booking_service import BookingService
from app.utils import http_bad_request

payment_page = Blueprint("payment_page", __name__)


@payment_page.route("/stripe")
def stripe_payment():
    return render_template("payment/stripe.html")


@payment_page.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")
    webhook_secret = current_app.config['STRIPE_WEBHOOK_SECRET']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return http_bad_request("Invalid payload")
    except stripe.error.SignatureVerificationError:
        return http_bad_request("Invalid signature")

    if event.type == 'checkout.session.completed':
        session = event.data.object

        if session.payment_status != 'paid':
            return "", 200

        data = session.metadata

        if data:
            booking = Booking.query.get(data.booking_id)
            if booking.expires_at <= datetime.now():
                stripe.Refund.create(
                    payment_intent=session.payment_intent
                )

                booking.status = BookingStatus.CANCELLED
                db.session.commit()
                return jsonify(success=True, message="Refunded"), 200

            tickets = []
            for seat in booking.seats_data:
                tickets.append(Ticket(
                    booking_id=booking.id,
                    seat_id=seat['id'],
                    price=seat['price']
                ))

            db.session.add_all(tickets)
            booking.status = BookingStatus.PAID

            db.session.commit()

            BookingService.delete_hold_seats(booking)

    elif event.type == 'checkout.session.expired':
        session = event.data.object

    return "", 200
