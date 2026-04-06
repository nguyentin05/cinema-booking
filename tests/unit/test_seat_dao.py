from datetime import datetime

import pytest

from app.daos import seat_dao
from app.models import SeatType, Room, Seat, PriceRule, DayOfWeek


@pytest.fixture
def sample_data(db_session):
    normal = SeatType(name="Normal")
    vip = SeatType(name="VIP")
    couple = SeatType(name="Couple")
    db_session.add_all([normal, vip, couple])
    db_session.flush()

    room1 = Room(name="Room 1", total_seats=5)
    room2 = Room(name="Room 2", total_seats=2)
    db_session.add_all([room1, room2])
    db_session.flush()

    seats_room1 = [
        Seat(seat_row="A", seat_number=1, room_id=room1.id, seat_type_id=normal.id),
        Seat(seat_row="A", seat_number=2, room_id=room1.id, seat_type_id=normal.id),
        Seat(seat_row="B", seat_number=1, room_id=room1.id, seat_type_id=vip.id),
        Seat(seat_row="B", seat_number=2, room_id=room1.id, seat_type_id=vip.id),
        Seat(seat_row="C", seat_number=1, room_id=room1.id, seat_type_id=couple.id),
    ]

    seats_room2 = [
        Seat(seat_row="A", seat_number=1, room_id=room2.id, seat_type_id=normal.id),
        Seat(seat_row="A", seat_number=2, room_id=room2.id, seat_type_id=vip.id),
    ]
    db_session.add_all(seats_room1 + seats_room2)
    db_session.flush()

    rules = [
        PriceRule(priority=0, price=50000),
        PriceRule(priority=1, day_of_week=DayOfWeek.SUNDAY, price=70000),
        PriceRule(priority=1, seat_type_id=vip.id, price=75000),
        PriceRule(priority=1, seat_type_id=couple.id, price=100000),
        PriceRule(priority=2, day_of_week=DayOfWeek.SUNDAY, seat_type_id=vip.id, price=95000),
        PriceRule(priority=2, day_of_week=DayOfWeek.SUNDAY, seat_type_id=couple.id, price=120000),
    ]
    db_session.add_all(rules)
    db_session.commit()

    return {
        "room1": room1, "room2": room2,
        "normal": normal, "vip": vip, "couple": couple,
        "seats_room1": seats_room1, "seats_room2": seats_room2,
    }


class TestGetSeatsByRoomId:

    def test_returns_all_seats_in_room(self, sample_data):
        room1_id = sample_data["room1"].id
        result = seat_dao.get_seats_by_room_id(room1_id)
        assert len(result) == 5

    def test_returns_correct_room(self, sample_data):
        room2_id = sample_data["room2"].id
        result = seat_dao.get_seats_by_room_id(room2_id)
        assert len(result) == 2
        assert all(s.room_id == room2_id for s in result)

    def test_ordered_by_row_then_number(self, sample_data):
        result = seat_dao.get_seats_by_room_id(sample_data["room1"].id)
        rows = [(s.seat_row, s.seat_number) for s in result]
        assert rows == sorted(rows)

    def test_joinedload_seat_type(self, sample_data):
        result = seat_dao.get_seats_by_room_id(sample_data["room1"].id)
        assert all(s.seat_type is not None for s in result)

    def test_returns_empty_for_invalid_room(self, sample_data):
        result = seat_dao.get_seats_by_room_id(12345678)
        assert result == []


class TestGetSeatsByIds:

    def test_returns_correct_seats(self, sample_data):
        seats = sample_data["seats_room1"]
        ids = [seats[0].id, seats[1].id]
        result = seat_dao.get_seats_by_ids(ids)
        assert len(result) == 2
        assert {s.id for s in result} == set(ids)

    def test_returns_empty_for_invalid_ids(self, sample_data):
        result = seat_dao.get_seats_by_ids([722, 227])
        assert result == []

    def test_partial_valid_ids(self, sample_data):
        valid_id = sample_data["seats_room1"][0].id
        result = seat_dao.get_seats_by_ids([valid_id, 10000001])
        assert len(result) == 1
        assert result[0].id == valid_id

    def test_ordered_by_row_then_number(self, sample_data):
        seats = sample_data["seats_room1"]
        ids = [s.id for s in seats]
        result = seat_dao.get_seats_by_ids(ids)
        rows = [(s.seat_row, s.seat_number) for s in result]
        assert rows == sorted(rows)

    def test_joinedload_seat_type(self, sample_data):
        ids = [sample_data["seats_room1"][0].id]
        result = seat_dao.get_seats_by_ids(ids)
        assert result[0].seat_type is not None


class TestGetPriceOfSeats:

    def test_normal_seat_weekday(self, sample_data):
        seats = seat_dao.get_seats_by_room_id(sample_data["room1"].id)
        normal_seats = [s for s in seats if s.seat_type.name == "Normal"]
        # Monday (2025-06-02 là thứ 2)
        result = seat_dao.get_price_of_seats(normal_seats, start_at=datetime(2025, 6, 2, 10, 0))
        for seat in normal_seats:
            assert result[seat.id] == 50000

    def test_vip_seat_weekday(self, sample_data):
        seats = seat_dao.get_seats_by_room_id(sample_data["room1"].id)
        vip_seats = [s for s in seats if s.seat_type.name == "VIP"]
        # Monday
        result = seat_dao.get_price_of_seats(vip_seats, start_at=datetime(2025, 6, 2, 10, 0))
        for seat in vip_seats:
            assert result[seat.id] == 75000

    def test_couple_seat_weekday(self, sample_data):
        seats = seat_dao.get_seats_by_room_id(sample_data["room1"].id)
        couple_seats = [s for s in seats if s.seat_type.name == "Couple"]
        # Monday
        result = seat_dao.get_price_of_seats(couple_seats, start_at=datetime(2025, 6, 2, 10, 0))
        for seat in couple_seats:
            assert result[seat.id] == 100000

    def test_normal_seat_sunday(self, sample_data):
        seats = seat_dao.get_seats_by_room_id(sample_data["room1"].id)
        normal_seats = [s for s in seats if s.seat_type.name == "Normal"]
        # Sunday (2025-06-01 là Chủ Nhật)
        result = seat_dao.get_price_of_seats(normal_seats, start_at=datetime(2025, 6, 1, 10, 0))
        for seat in normal_seats:
            assert result[seat.id] == 70000

    def test_vip_seat_sunday(self, sample_data):
        seats = seat_dao.get_seats_by_room_id(sample_data["room1"].id)
        vip_seats = [s for s in seats if s.seat_type.name == "VIP"]
        # Sunday
        result = seat_dao.get_price_of_seats(vip_seats, start_at=datetime(2025, 6, 1, 10, 0))
        for seat in vip_seats:
            assert result[seat.id] == 95000

    def test_couple_seat_sunday(self, sample_data):
        seats = seat_dao.get_seats_by_room_id(sample_data["room1"].id)
        couple_seats = [s for s in seats if s.seat_type.name == "Couple"]
        # Sunday
        result = seat_dao.get_price_of_seats(couple_seats, start_at=datetime(2025, 6, 1, 10, 0))
        for seat in couple_seats:
            assert result[seat.id] == 120000

    def test_returns_price_for_all_seats(self, sample_data):
        seats = seat_dao.get_seats_by_room_id(sample_data["room1"].id)
        result = seat_dao.get_price_of_seats(seats, start_at=datetime(2025, 6, 2, 10, 0))
        assert len(result) == len(seats)
        assert all(seat.id in result for seat in seats)

    def test_returns_empty_for_no_seats(self, sample_data):
        result = seat_dao.get_price_of_seats([])
        assert result == {}
