from datetime import datetime, timedelta

from flask import current_app

from app import db
from app.daos import seat_dao, ticket_dao
from app.models import Ticket, Booking, TicketStatus, Seat, Showtime


class BookingService:
    @staticmethod
    def booking_seats(user_id, showtime_id, seat_ids):
        showtime = Showtime.query.get(showtime_id)
        if not showtime:
            raise ValueError("This showtime do not exist")

        now = datetime.now()
        if showtime.start_at <= now:
            raise ValueError("Showtime has already started")

        max_booking = current_app.config.get("MAX_BOOKING_SEAT_EACH_SHOWTIME")
        if len(seat_ids) > max_booking:
            raise ValueError(f"You can only book a maximum of {max_booking} seats per showtime.")

        booked_tickets = (
            db.session.query(Ticket.seat_id)
            .join(Booking, Ticket.booking_id == Booking.id)
            .filter(
                Booking.showtime_id == showtime_id,
                Ticket.seat_id.in_(seat_ids),
                Ticket.status != TicketStatus.CANCELLED.name,
                Booking.expires_at > now
            )
            .all()
        )

        if booked_tickets:
            conflict_seat_ids = [ticket[0] for ticket in booked_tickets]
            booked_seat_names = [f"{row}{number}" for row, number in (db.session.query(Seat.seat_row, Seat.seat_number)
                                                                      .filter(Seat.id.in_(conflict_seat_ids))
                                                                      .all())]
            seats_str = ", ".join(booked_seat_names)
            raise ValueError(f"The following seats are already booked: {seats_str}")

        already_booked_seats = ticket_dao.count_seats_of_showtime_booked_by_user(
            showtime_id=showtime_id,
            user_id=user_id)

        if already_booked_seats + len(seat_ids) > max_booking:
            raise ValueError(f"You can only book a maximum of {max_booking} seats per showtime.")

        seats = seat_dao.get_seats_by_ids(seat_ids)
        s_id_not_in_room = []
        for seat in seats:
            if seat.room_id != showtime.room_id:
                s_id_not_in_room.append(seat.id)

        if s_id_not_in_room:
            raise ValueError(f"Seat ids: {s_id_not_in_room} not in this room")

        # After validate successfully create booking and tickets
        seat_price_map = seat_dao.get_price_of_seats(seats, {"start_at": showtime.start_at})
        total_price = sum(price for price in seat_price_map.values())
        booking = Booking(
            user_id=user_id,
            showtime_id=showtime_id,
            expires_at=now + timedelta(minutes=10),
            total_price=total_price
        )
        db.session.add(booking)
        db.session.flush()

        tickets = []
        for seat in seats:
            tickets.append(Ticket(
                booking_id=booking.id,
                seat_id=seat.id,
                price=seat_price_map.get(seat.id)
            ))

        db.session.add_all(tickets)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
