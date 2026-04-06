from abc import ABC, abstractmethod
from datetime import datetime

import stripe.checkout
from flask import current_app

from app.models import Booking, BookingStatus


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
