from sqlalchemy import func

from app import db
from app.models import Ticket, Booking


def count_seats_of_showtime_booked_by_user(showtime_id, user_id):
    already_booked_seats = (
        db.session.query(func.count(Ticket.id))
        .join(Booking, Ticket.booking_id == Booking.id)
        .filter(
            Booking.showtime_id == showtime_id,
            Booking.user_id == user_id
        )
        .scalar()
    )

    return already_booked_seats or 0
