from sqlalchemy import func

from app import db
from app.models import Ticket, Booking, TicketStatus


def count_active_tickets_of_user(user_id):
    res = (
        db.session.query(func.count(Ticket.id))
        .join(Booking, Ticket.booking_id == Booking.id)
        .filter(
            Booking.user_id == user_id,
            Ticket.status == TicketStatus.ACTIVE)
        .scalar()
    )

    return res or 0
