import secrets
from datetime import datetime, timedelta

import pytest

from app.daos import ticket_dao
from app.models import User, SeatType, Room, Seat, Movie, Showtime, Booking, BookingStatus, Ticket
from app.models.ticket import TicketStatus


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

    user1 = User(email="user@test.com", name="User", password="123456")
    db_session.add(user1)
    db_session.flush()

    booking = Booking(
        user_id=user1.id, showtime_id=showtime.id,
        total_seats=3, seats_data=[],
        status=BookingStatus.PAID,
        expires_at=datetime.now() + timedelta(minutes=30),
    )
    db_session.add(booking)
    db_session.flush()

    # 2 active, 1 inactive
    tickets = [
        Ticket(booking_id=booking.id, seat_id=seats[0].id, price=50000, status=TicketStatus.ACTIVE,
               secret_code=secrets.token_urlsafe(16)),
        Ticket(booking_id=booking.id, seat_id=seats[1].id, price=50000, status=TicketStatus.USED,
               secret_code=secrets.token_urlsafe(16)),
        Ticket(booking_id=booking.id, seat_id=seats[2].id, price=50000, status=TicketStatus.CANCELLED,
               secret_code=secrets.token_urlsafe(16)),
    ]
    db_session.add_all(tickets)

    user2 = User(email="user2@test.com", name="user2", password="123")
    db_session.add(user2)
    db_session.flush()
    b2 = Booking(user_id=user2.id,
                 showtime_id=showtime.id,
                 total_seats=3, seats_data=[],
                 status=BookingStatus.PAID,
                 expires_at=datetime.now() + timedelta(minutes=30))
    db_session.add(b2)
    db_session.flush()
    tickets2 = [
        Ticket(booking_id=b2.id, seat_id=seats[0].id, price=50000, status=TicketStatus.ACTIVE,
               secret_code=secrets.token_urlsafe(16)),
        Ticket(booking_id=b2.id, seat_id=seats[1].id, price=50000, status=TicketStatus.ACTIVE,
               secret_code=secrets.token_urlsafe(16)),
        Ticket(booking_id=b2.id, seat_id=seats[2].id, price=50000, status=TicketStatus.ACTIVE,
               secret_code=secrets.token_urlsafe(16)),
    ]
    db_session.add_all(tickets2)

    db_session.commit()

    return {
        "user1": user1,
        "user2": user2,
        "tickets1": tickets,
        "tickets2": tickets2
    }


class TestCountTicketsOfUser:

    def test_count_only_active_tickets(self, sample_data):
        user1, user2 = sample_data["user1"], sample_data["user2"]
        res1 = ticket_dao.count_active_tickets_of_user(user1.id)
        res2 = ticket_dao.count_active_tickets_of_user(user2.id)
        assert res1 == 1
        assert res2 == 3

    def test_after_cancel_ticket(self, sample_data, db_session):
        user1 = sample_data['user1']
        user2 = sample_data['user2']
        ticket1_list = sample_data['tickets1']

        initial_count_u1 = ticket_dao.count_active_tickets_of_user(user1.id)
        initial_count_u2 = ticket_dao.count_active_tickets_of_user(user2.id)

        ticket_to_cancel = [t for t in ticket1_list if t.status == TicketStatus.USED][0]
        ticket_to_cancel.status = TicketStatus.CANCELLED

        db_session.add(ticket_to_cancel)
        db_session.commit()

        new_count_u1 = ticket_dao.count_active_tickets_of_user(user1.id)
        new_count_u2 = ticket_dao.count_active_tickets_of_user(user2.id)

        assert new_count_u1 == initial_count_u1

        assert new_count_u2 == initial_count_u2

    def test_returns_zero_for_unknown_user(self, sample_data):
        result = ticket_dao.count_active_tickets_of_user(897)
        assert result == 0

    def test_returns_int_not_none(self, sample_data):
        result = ticket_dao.count_active_tickets_of_user(324)
        assert isinstance(result, int)
