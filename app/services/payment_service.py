from abc import ABC, abstractmethod
from datetime import datetime

import stripe.checkout
from flask import current_app

from app.models import Booking


class PaymentService(ABC):
    @staticmethod
    def _validate_booking(booking_id):
        booking = Booking.query.get(booking_id)
        if not booking:
            raise ValueError("This booking do not exists")

        if booking.expires_at <= datetime.now():
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
                        'name': f'Vé xem phim: ',
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
            return_url=kwargs.get("return_url", "http://localhost:5000")
        )

        return {
            "client_secret": checkout_session.client_secret,
            "public_key": self.public_key
        }


_factory = {}


def get_payment_service(method) -> PaymentService:
    global _factory

    if not _factory:
        _factory = {
            'stripe': StripePaymentService()
        }

    return _factory[method]
