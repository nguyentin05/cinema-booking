from datetime import datetime

from sqlalchemy import func

from app import db
from app.models import Booking, BookingStatus


def count_booking_pending_of_user(user_id):
    res = (
        db.session.query(func.count(Booking.id))
        .filter(Booking.status == BookingStatus.PENDING, Booking.expires_at > datetime.now())
        .scalar()
    )

    return res or 0
