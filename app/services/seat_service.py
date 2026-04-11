from flask import current_app
from werkzeug.exceptions import NotFound, Conflict

from app import db
from app.daos import seat_dao
from app.dtos import SeatDTO
from app.models import Showtime, Ticket, Booking, TicketStatus
from app.utils import get_redis


class SeatService:
    @staticmethod
    def get_seats_of_showtime(showtime_id):
        showtime = Showtime.query.get(showtime_id)
        if not showtime:
            raise NotFound("Showtime does not exist")

        booked_seat_ids = (db.session.query(Ticket.seat_id).join(
            Booking, Ticket.booking_id == Booking.id
        ).filter(
            Booking.showtime_id == showtime_id,
            Ticket.status != TicketStatus.CANCELLED
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

    @staticmethod
    def hold_seat_for_booking(booking):
        booking_expiration_time = current_app.config.get("BOOKING_EXPIRATION_TIME")
        redis_client = get_redis()
        pipe = redis_client.pipeline()
        seat_keys = {
            seat['id']: f"hold:showtime:{booking.showtime_id}:seat:{seat['id']}"
            for seat in booking.seats_data
        }
        user_key = f"hold:user:{booking.user_id}:booking_id"
        for seat_id, key in seat_keys.items():
            pipe.set(key, seat_id, ex=booking_expiration_time, nx=True)

        pipe.set(user_key, booking.id, ex=booking_expiration_time, nx=True)
        results = pipe.execute()

        if not all(results):
            seat_results = results[:-1]
            user_key_success = results[-1]
            keys_to_delete = []

            for seat, success in zip(booking.seats_data, seat_results):
                if success:
                    keys_to_delete.append(seat_keys[seat['id']])

            if user_key_success:
                keys_to_delete.append(user_key)

            if keys_to_delete:
                redis_client.delete(*keys_to_delete)

            if not user_key_success:
                raise Conflict("You already have a pending booking in progress. Please complete or cancel it first.")

            failed_seats = [
                seat['name']
                for seat, success in zip(booking.seats_data, seat_results)
                if not success
            ]
            seats_str = ", ".join(failed_seats)
            raise Conflict(f"Seats are no longer available: {seats_str}")

    @staticmethod
    def delete_hold_seats_of_booking(booking):
        redis_client = get_redis()
        redis_client.delete(f"hold:user:{booking.user_id}:booking_id")
        hold_seat_keys = [f"hold:showtime:{booking.showtime_id}:seat:{seat['id']}" for seat in booking.seats_data]
        if hold_seat_keys:
            redis_client.delete(*hold_seat_keys)
