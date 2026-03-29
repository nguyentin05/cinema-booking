from datetime import datetime

from sqlalchemy import desc, or_
from sqlalchemy.orm import joinedload

from app.models import PriceRule, DayOfWeek, Seat


def get_seats_by_room_id(room_id):
    return (Seat.query
            .options(joinedload(Seat.seat_type))
            .filter(Seat.room_id == room_id)
            .order_by(Seat.seat_row, Seat.seat_number)
            .all())


def get_seats_by_ids(seat_ids):
    return (Seat.query
            .options(joinedload(Seat.seat_type))
            .filter(Seat.id.in_(seat_ids))
            .order_by(Seat.seat_row, Seat.seat_number)
            .all())


def get_price_of_seats(seats, args):
    start_at = args.get('start_at', datetime.now())
    day_of_week = DayOfWeek(start_at.isoweekday())
    price_rules = PriceRule.query.filter(
        or_(
            PriceRule.day_of_week == day_of_week,
            PriceRule.day_of_week.is_(None)
        )
    ).order_by(desc(PriceRule.priority)).all()
    res = {}

    for seat in seats:
        for rule in price_rules:
            is_valid_seat = (rule.seat_type_id == seat.seat_type_id or rule.seat_type_id is None)

            if is_valid_seat:
                res[seat.id] = rule.price
                break

    return res
