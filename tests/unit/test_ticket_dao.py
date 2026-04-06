from datetime import datetime, timedelta

import pytest

from app.daos import ticket_dao
from app.models import User, SeatType, Room, Seat, Movie, Showtime, Booking, BookingStatus, Ticket


@pytest.fixture
def sample_data(db_session):
    seat_type = SeatType(name="Normal")
    room = Room(name="Room 1", total_seats=3)
    db_session.add_all([seat_type, room])
    db_session.flush()

    seats = [
        Seat(seat_row="A", seat_number=i, room_id=room.id, seat_type_id=seat_type.id)
        for i in range(1, 4)
    ]
    db_session.add_all(seats)
    db_session.flush()

    movie = Movie(title="Test Movie", duration_minutes=120)
    db_session.add(movie)
    db_session.flush()

    showtime = Showtime(
        movie_id=movie.id, room_id=room.id,
        start_at=datetime(2025, 6, 1, 10, 0),
        end_at=datetime(2025, 6, 1, 12, 0)
    )
    db_session.add(showtime)
    db_session.flush()

    user = User(email="user@test.com", name="User", password="123456")
    db_session.add(user)
    db_session.flush()

    booking = Booking(
        user_id=user.id, showtime_id=showtime.id,
        total_seats=3, seats_data=[],
        status=BookingStatus.PAID,
        expires_at=datetime.now() + timedelta(minutes=30)
    )
    db_session.add(booking)
    db_session.flush()

    # 2 active, 1 inactive
    tickets = [
        Ticket(booking_id=booking.id, seat_id=seats[0].id, price=50000, is_active=True),
        Ticket(booking_id=booking.id, seat_id=seats[1].id, price=50000, is_active=True),
        Ticket(booking_id=booking.id, seat_id=seats[2].id, price=50000, is_active=False),
    ]
    db_session.add_all(tickets)
    db_session.commit()

    return {"user": user}


class TestCountTicketsOfUser:

    def test_count_only_active_tickets(self, sample_data):
        result = ticket_dao.count_tickets_of_user(sample_data["user"].id)
        assert result == 2

    def test_returns_zero_for_unknown_user(self, sample_data):
        result = ticket_dao.count_tickets_of_user(897)
        assert result == 0

    def test_returns_int_not_none(self, sample_data):
        result = ticket_dao.count_tickets_of_user(324)
        assert isinstance(result, int)
