from datetime import datetime

from sqlalchemy import desc, or_
from sqlalchemy.orm import joinedload

from app import db
from app.dtos import SeatDTO
from app.models import Showtime, Seat, Ticket, Booking, TicketStatus, PriceRule, DayOfWeek, SeatType


def get_seats_of_showtime(showtime_id):
    showtime = Showtime.query.get(showtime_id)
    if not showtime:
        raise ValueError("Showtime does not exist")

    seat_type_map = {st.id: st for st in SeatType.query.all()}

    seat_type_price_map = _get_prices_for_seats([id for id in seat_type_map.keys()], showtime.start_at)

    tickets = (db.session.query(Ticket.seat_id, Ticket.status).join(
        Booking, Ticket.booking_id == Booking.id
    ).filter(
        Booking.showtime_id == showtime_id,
        Ticket.status != TicketStatus.CANCELLED.name
    ).all())

    seat_status_map = {t.seat_id: t.status.name for t in tickets}

    seats = (Seat.query
             .filter(Seat.room_id == showtime.room_id)
             .order_by(Seat.seat_row, Seat.seat_number)
             .all())

    res = []
    for seat in seats:
        seat_type = seat_type_map[seat.seat_type_id]
        res.append(SeatDTO(
            id=seat.id,
            row=seat.seat_row,
            number=seat.seat_number,
            type=seat_type.name,
            status=seat_status_map.get(seat.id, "AVAILABLE"),
            price=seat_type_price_map.get(seat_type.id, 50000)
        ))

    return res


def _get_prices_for_seats(seat_type_ids: list, start_at):
    day_of_week = DayOfWeek(start_at.isoweekday())
    price_rules = PriceRule.query.order_by(desc(PriceRule.priority)).all()
    seat_type_price_map = {}

    for st_id in seat_type_ids:
        for rule in price_rules:
            is_valid_day = (rule.day_of_week == day_of_week or rule.day_of_week is None)
            is_valid_seat = (rule.seat_type_id == st_id or rule.seat_type_id is None)

            if is_valid_day and is_valid_seat:
                seat_type_price_map[st_id] = rule.price
                break

    return seat_type_price_map
