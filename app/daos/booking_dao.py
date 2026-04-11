from sqlalchemy import func

from app import db
from app.models import Booking
from app.utils import get_redis


def count_booked_seats_by_user(user_id, showtime_id):
    res = (
        db.session.query(func.sum(Booking.total_seats))
        .filter(
            Booking.user_id == user_id,
            Booking.showtime_id == showtime_id
        )
        .scalar()
    )

    return res or 0


def get_booking_in_progress_of_user(user_id):
    redis_client = get_redis()
    booking_id = redis_client.get(f"hold:user:{user_id}:booking_id")
    if booking_id:
        booking = Booking.query.get(booking_id)
        return {
            "id": booking.id,
            "seats_data": booking.seats_data,
            "total_seats": booking.total_seats,
            "total_price": booking.total_price,
            "expires_at": booking.expires_at.isoformat()
        }

    return None
