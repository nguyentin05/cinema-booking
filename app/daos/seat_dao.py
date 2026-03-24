from sqlalchemy.orm import joinedload

from app import db
from app.dtos import SeatDTO
from app.models import Showtime, Seat, Ticket, Booking, TicketStatus


def get_seats_of_showtime(showtime_id):
    showtime = Showtime.query.get(showtime_id)
    if not showtime:
        raise ValueError("Showtime does not exist")

    seats = (Seat.query
             .options(joinedload(Seat.seat_type))
             .filter(Seat.room_id == showtime.room_id)
             .order_by(Seat.seat_row, Seat.seat_number)
             .all())

    tickets = (db.session.query(Ticket.seat_id, Ticket.status).join(
        Booking, Ticket.booking_id == Booking.id
    ).filter(
        Booking.showtime_id == showtime_id,
        Ticket.status != TicketStatus.CANCELLED.name
    ).all())

    seat_status_map = {t.seat_id: t.status for t in tickets}

    res = []
    for seat in seats:
        status = seat_status_map.get(seat.id)

        res.append(SeatDTO(
            id=seat.id,
            row=seat.seat_row,
            number=seat.seat_number,
            type=seat.seat_type.name,
            status=status.name if status else "AVAILABLE"
        ))

    return res
