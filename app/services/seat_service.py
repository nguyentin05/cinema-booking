from app import db
from app.daos import seat_dao
from app.dtos import SeatDTO
from app.models import Showtime, Ticket, Booking
from app.utils import get_redis


class SeatService:
    @staticmethod
    def get_seats_of_showtime(showtime_id):
        showtime = Showtime.query.get(showtime_id)
        if not showtime:
            raise ValueError("Showtime does not exist")

        booked_seat_ids = (db.session.query(Ticket.seat_id).join(
            Booking, Ticket.booking_id == Booking.id
        ).filter(
            Booking.showtime_id == showtime_id,
            Ticket.is_active.is_(True)
        ).all())
        booked_seat_ids = {row[0] for row in booked_seat_ids}

        redis_client = get_redis()
        hold_seat_keys = list(redis_client.scan_iter(f"hold:showtime:{showtime_id}:seat:*"))
        hold_seat_ids = set()
        if hold_seat_keys:
            hold_seat_values = redis_client.mget(hold_seat_keys)
            hold_seat_ids = {int(id) for id in hold_seat_values if id is not None}

        seats = seat_dao.get_seats_by_room_id(showtime.room_id)
        seat_price_map = seat_dao.get_price_of_seats(seats, start_at=showtime.start_at)
        res = []

        for seat in seats:
            res.append(SeatDTO(
                id=seat.id,
                row=seat.seat_row,
                number=seat.seat_number,
                type=seat.seat_type.name,
                status="PAID" if seat.id in booked_seat_ids else "HOLDING" if seat.id in hold_seat_ids else "AVAILABLE",
                price=seat_price_map.get(seat.id, 50000)
            ))

        return res
