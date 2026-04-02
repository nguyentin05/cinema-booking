from datetime import datetime

from app import db
from app.models import Booking, BookingStatus


def get_pending_booking_of_user(user_id):
    res = (db.session.query(Booking.id, Booking.expires_at)
    .filter(
        Booking.user_id == user_id,
        Booking.status == BookingStatus.PENDING.name,
        Booking.expires_at > datetime.now()
    )).first()

    if res:
        return True, res.id, res.expires_at.isoformat()

    return False, None, None
