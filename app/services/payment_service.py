from abc import ABC, abstractmethod
from datetime import datetime

import stripe.checkout
from flask import current_app

from app import db
from app.models import Booking, BookingStatus, Ticket
from app.services.seat_service import SeatService


class PaymentService(ABC):
    @staticmethod
    def _validate_booking(booking_id):
        booking = Booking.query.get(booking_id)
        if not booking:
            raise ValueError("This booking do not exists")

        if booking.expires_at <= datetime.now() or booking.status == BookingStatus.CANCELLED:
            raise ValueError("This booking has expired.")

        return booking

    def process_payment(self, booking_id, **kwargs):
        booking = PaymentService._validate_booking(booking_id)
        return self.process(booking, **kwargs)

    @abstractmethod
    def process(self, booking, **kwargs):
        pass


class StripePaymentService(PaymentService):
    def __init__(self):
        self.public_key = current_app.config.get("STRIPE_PUBLIC_KEY")

    def process(self, booking, **kwargs):
        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                    'currency': 'vnd',
                    'product_data': {
                        'name': 'Vé xem phim: ',
                    },
                    'unit_amount': int(booking.total_price),
                },
                'quantity': 1,
            }],
            mode='payment',
            ui_mode='embedded_page',
            metadata={
                "booking_id": booking.id,
            },
            return_url=kwargs.get("return_url", "http://127.0.0.1:5000")
        )

        return {
            "client_secret": checkout_session.client_secret,
            "public_key": self.public_key
        }

    @staticmethod
    def verify_event(payload, sig_header, webhook_secret):
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            return event
        except ValueError:
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid signature")

    @staticmethod
    def handle_expired_booking(booking, session):
        stripe.Refund.create(payment_intent=session.payment_intent)
        if booking.status == BookingStatus.PENDING:
            booking.status = BookingStatus.CANCELLED

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def handle_successful_payment(session):
        data = session.metadata
        if not data:
            raise ValueError("Missing metadata")

        booking = Booking.query.get(data.booking_id)
        if booking.expires_at <= datetime.now() or booking.status == BookingStatus.CANCELLED:
            StripePaymentService.handle_expired_booking(booking, session)
            return

        tickets = [
            Ticket(booking_id=booking.id, seat_id=seat['id'], price=seat['price'])
            for seat in booking.seats_data
        ]
        db.session.add_all(tickets)
        booking.status = BookingStatus.PAID

        try:
            db.session.commit()
            SeatService.delete_hold_seats_of_booking(booking)
        except Exception:
            db.session.rollback()
            raise


class PaymentServiceFactory:
    _payment_services = {
        'stripe': StripePaymentService
    }

    @staticmethod
    def get(method) -> PaymentService | None:
        service_class = PaymentServiceFactory._payment_services.get(method)
        if not service_class:
            return None
        return service_class()
