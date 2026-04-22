import secrets
from abc import ABC, abstractmethod
from datetime import datetime

import stripe.checkout
from flask import current_app
from werkzeug.exceptions import BadRequest

from app import db, cache
from app.exceptions import BookingHasExpired, BookingHasCancelled
from app.models import Booking, BookingStatus, Ticket
from app.services.seat_service import SeatService


class PaymentService(ABC):
    @staticmethod
    def _validate_booking(booking_id):
        booking = Booking.query.get(booking_id)
        if not booking:
            raise BadRequest("This booking do not exists")

        if booking.expires_at <= datetime.now():
            raise BookingHasExpired()

        if booking.status == BookingStatus.CANCELLED:
            raise BookingHasCancelled()

        if booking.status == BookingStatus.PAID:
            raise BadRequest("This booking has already been paid")

        return booking

    def process_payment(self, booking_id, **kwargs):
        booking = PaymentService._validate_booking(booking_id)
        return self.process(booking, **kwargs)

    @abstractmethod
    def process(self, booking, **kwargs):
        pass

    def handle_callback(self, booking_id, **kwargs):
        try:
            booking = PaymentService._validate_booking(booking_id)
        except (BookingHasExpired, BookingHasCancelled):
            self.handle_expired_or_cancelled_booking(booking_id, **kwargs)
            return
        except BadRequest as e:
            if "already been paid" in str(e.description):
                return
            raise
        except Exception:
            raise

        booking.status = BookingStatus.PAID
        tickets = []
        for seat_data in booking.seats_data:
            tickets.append(Ticket(
                booking_id=booking.id,
                seat_id=seat_data['id'],
                price=seat_data['price'],
                secret_code=secrets.token_urlsafe(16)
            ))

        db.session.add_all(tickets)

        try:
            db.session.commit()
            SeatService.delete_hold_seats_of_booking(booking)
            cache.delete(f"count_active_tickets_of_user:user_id:{booking.user_id}")
        except Exception:
            db.session.rollback()
            raise

    @abstractmethod
    def handle_expired_or_cancelled_booking(self, booking_id, **kwargs):
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
            raise BadRequest("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise BadRequest("Invalid signature")

    def handle_expired_or_cancelled_booking(self, booking_id, **kwargs):
        session = kwargs.get('session')
        stripe.Refund.create(payment_intent=session.payment_intent)

        booking_status = db.session.query(Booking.status).filter(Booking.id == booking_id).scalar()
        if booking_status == BookingStatus.CANCELLED:
            return

        Booking.query.filter(Booking.id == booking_id).update({
            'status': BookingStatus.CANCELLED.name
        })

        try:
            db.session.commit()
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
