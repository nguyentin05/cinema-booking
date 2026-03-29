from sqlalchemy.orm import joinedload

from app import db
from app.daos import seat_dao
from app.dtos import SeatDTO
from app.models import Showtime, Ticket, Booking, TicketStatus


class SeatService:
    @staticmethod
    def get_seats_of_showtime(showtime_id):
        showtime = Showtime.query.get(showtime_id)
        if not showtime:
            raise ValueError("Showtime does not exist")

        tickets = (db.session.query(Ticket.seat_id, Ticket.status).join(
            Booking, Ticket.booking_id == Booking.id
        ).filter(
            Booking.showtime_id == showtime_id,
            Ticket.status != TicketStatus.CANCELLED.name
        ).all())

        seat_status_map = {t.seat_id: t.status.name for t in tickets}
        seats = seat_dao.get_seats_by_room_id(showtime.room_id)
        seat_price_map = seat_dao.get_price_of_seats(seats, {"start_at": showtime.start_at})
        res = []

        for seat in seats:
            res.append(SeatDTO(
                id=seat.id,
                row=seat.seat_row,
                number=seat.seat_number,
                type=seat.seat_type.name,
                status=seat_status_map.get(seat.id, "AVAILABLE"),
                price=seat_price_map.get(seat.id, 50000)
            ))

        return res
