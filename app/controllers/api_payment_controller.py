from datetime import datetime

import stripe
from flask import Blueprint, request, jsonify, current_app

from app import db
from app.decorators import api_login_required
from app.models import Booking, BookingStatus, Ticket
from app.services.payment_service import PaymentServiceFactory
from app.services.seat_service import SeatService
from app.utils import http_bad_request, http_internal_server_error

api_payment = Blueprint("api_payment", __name__)


@api_payment.route('/', methods=['POST'])
@api_login_required
def pay():
    data = request.get_json()
    method = data.get('method')
    booking_id = data.get('booking_id')

    service = PaymentServiceFactory.get(method)
    if not service:
        return http_bad_request("method must be: 'stripe' or 'momo'")

    try:
        res = {}
        if method == 'stripe':
            return_url = data.get('return_url', request.host_url)
            res = service.process_payment(booking_id, return_url=return_url)
        res['method'] = method
        return jsonify(res), 200
    except ValueError as ex:
        return http_bad_request(message=str(ex))
    except Exception as ex:
        return http_internal_server_error(ex)


@api_payment.route('/stripe/callback', methods=['POST'])
def stripe_callback():
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
            if booking.expires_at <= datetime.now() or booking.status == BookingStatus.CANCELLED:
                stripe.Refund.create(
                    payment_intent=session.payment_intent
                )

                if booking.status == BookingStatus.PENDING:
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

            SeatService.delete_hold_seats_of_booking(booking)

    elif event.type == 'checkout.session.expired':
        session = event.data.object

    return "", 200
