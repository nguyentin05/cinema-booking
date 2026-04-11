from datetime import datetime, timedelta

from flask import current_app
from werkzeug.exceptions import NotFound, BadRequest, Conflict, Forbidden

from app import db
from app.daos import seat_dao, booking_dao
from app.models import Ticket, Booking, Showtime, BookingStatus, TicketStatus
from app.services.seat_service import SeatService
from app.utils import get_redis


class BookingService:
    @staticmethod
    def booking_seats(user_id, showtime_id, seat_ids):
        showtime = Showtime.query.get(showtime_id)
        if not showtime:
            raise NotFound("This showtime do not exist")

        redis_client = get_redis()
        existing_booking_id = redis_client.get(f"hold:user:{user_id}:booking_id")
        if existing_booking_id:
            raise Conflict(f"You have an existing unpaid booking_id: {existing_booking_id}")

        now = datetime.now()
        if showtime.start_at <= now:
            raise BadRequest("Showtime has already started")

        max_booking = current_app.config.get("MAX_BOOKING_SEAT_EACH_SHOWTIME")
        if len(seat_ids) > max_booking:
            raise BadRequest(f"You can only book a maximum of {max_booking} seats per showtime.")

        seats_map = {seat.id: seat for seat in seat_dao.get_seats_by_ids(seat_ids)}

        booked_seat_ids = (
            db.session.query(Ticket.seat_id)
            .join(Booking, Ticket.booking_id == Booking.id)
            .filter(
                Booking.showtime_id == showtime_id,
                Ticket.seat_id.in_(seat_ids),
                Ticket.status != TicketStatus.CANCELLED
            )
            .all()
        )

        hold_seat_keys = [f"hold:showtime:{showtime_id}:seat:{id}" for id in seat_ids]
        hold_seat_values = redis_client.mget(hold_seat_keys)
        hold_seat_ids = [int(id) for id in hold_seat_values if id is not None]

        if booked_seat_ids or hold_seat_ids:
            conflict_seat_ids = [ticket[0] for ticket in booked_seat_ids] + hold_seat_ids
            booked_seat_names = [
                f"{seats_map[s_id].seat_row}{seats_map[s_id].seat_number}" for s_id in conflict_seat_ids
            ]
            seats_str = ", ".join(booked_seat_names)
            raise Conflict(f"The following seats are already booked: {seats_str}")

        already_booked_seats = booking_dao.count_booked_seats_by_user(user_id=user_id, showtime_id=showtime_id)

        if already_booked_seats + len(seat_ids) > max_booking:
            raise BadRequest(f"You can only book a maximum of {max_booking} seats per showtime.")

        s_id_not_in_room = [
            s_id for s_id in seat_ids
            if s_id not in seats_map or seats_map[s_id].room_id != showtime.room_id
        ]
        if s_id_not_in_room:
            raise BadRequest(f"Seat ids: {s_id_not_in_room} not in this room")

        # After validate successfully create booking and tickets
        booking_expiration_time = current_app.config.get("BOOKING_EXPIRATION_TIME")
        seat_price_map = seat_dao.get_price_of_seats(seats_map.values(), start_at=showtime.start_at)
        total_price = sum(price for price in seat_price_map.values())
        seats_data = [
            {"id": seat.id,
             "name": f"{seat.seat_row}{seat.seat_number}",
             "price": seat_price_map.get(seat.id)}
            for seat in seats_map.values()
        ]
        booking = Booking(
            user_id=user_id,
            showtime_id=showtime_id,
            expires_at=now + timedelta(seconds=booking_expiration_time),
            total_price=total_price,
            total_seats=len(seat_ids),
            seats_data=seats_data
        )
        db.session.add(booking)

        try:
            db.session.commit()
            SeatService.hold_seat_for_booking(booking)
            return booking
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def cancel_booking(user_id, booking_id):
        booking = Booking.query.get(booking_id)
        if not booking:
            raise NotFound("This booking does not exist")

        if booking.user_id != user_id:
            raise Forbidden("You are not allowed to cancel this booking")

        booking.status = BookingStatus.CANCELLED

        SeatService.delete_hold_seats_of_booking(booking)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
