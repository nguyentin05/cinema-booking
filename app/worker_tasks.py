from datetime import datetime

from celery import shared_task

from app import db
from app.models import Booking, BookingStatus


@shared_task(bind=True, max_retries=3)
def cancel_booking_expired(self, booking_id):
    booking = Booking.query.get(booking_id)
    if (not booking or
            (booking.expires_at > datetime.now()) or
            (booking.status == BookingStatus.PAID) or
            (booking.status == BookingStatus.CANCELLED)):
        return

    booking.status = BookingStatus.CANCELLED

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise self.retry(exc=e, countdown=5)
