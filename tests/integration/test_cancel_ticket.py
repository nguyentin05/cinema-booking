import secrets
from datetime import datetime, timedelta

import pytest

from app.models import Booking, BookingStatus, Ticket, TicketStatus, Showtime
from app.models import Movie, Seat, SeatType, Room, PriceRule

@pytest.fixture
def test_data(db_session):
    movie = Movie(title="Test Movie", duration_minutes=120)
    seat_type = SeatType(name="Normal")
    room = Room(name="Room 01", total_seats=10)
    db_session.add_all([movie, seat_type, room])
    db_session.flush()

    seats = []
    for i in range(1, 11):
        seat = Seat(seat_row="A", seat_number=i, room_id=room.id, seat_type_id=seat_type.id)
        seats.append(seat)

    room2 = Room(name="Room 02", total_seats=5)
    db_session.add(room2)
    db_session.flush()
    other_room_seat = Seat(seat_row="B", seat_number=1, room_id=room2.id, seat_type_id=seat_type.id)
    db_session.add(other_room_seat)

    price_rule = PriceRule(priority=0, price=50000)
    db_session.add(price_rule)

    future_showtime = Showtime(
        movie_id=movie.id,
        room_id=room.id,
        start_at=datetime.now() + timedelta(hours=24),
        end_at=datetime.now() + timedelta(hours=26),
    )
    past_showtime = Showtime(
        movie_id=movie.id,
        room_id=room.id,
        start_at=datetime.now() - timedelta(hours=1),
        end_at=datetime.now() + timedelta(hours=1),
    )
    far_future_showtime = Showtime(
        movie_id=movie.id,
        room_id=room.id,
        start_at=datetime.now() + timedelta(hours=10),
        end_at=datetime.now() + timedelta(hours=12),
    )
    close_showtime = Showtime(
        movie_id=movie.id,
        room_id=room.id,
        start_at=datetime.now() + timedelta(hours=1, minutes=30),
        end_at=datetime.now() + timedelta(hours=3, minutes=30),
    )
    db_session.add_all(seats)
    db_session.add_all([future_showtime, past_showtime, far_future_showtime, close_showtime])
    db_session.commit()

    return {
        "seats": seats,
        "other_room_seat": other_room_seat,
        "future_showtime": future_showtime,
        "past_showtime": past_showtime,
        "far_future_showtime": far_future_showtime,
        "close_showtime": close_showtime,
        "movie": movie,
        "room": room,
    }

@pytest.fixture
def create_paid_booking(db_session, test_data):
    def create(seat_ids, showtime=None, user=None):
        showtime = showtime or test_data["far_future_showtime"]
        seats = [s for s in test_data["seats"] if s.id in seat_ids]
        booking = Booking(
            user_id=user.id,
            showtime_id=showtime.id,
            total_price=50000 * len(seat_ids),
            total_seats=len(seat_ids),
            seats_data=[
                {"id": s.id, "name": f"{s.seat_row}{s.seat_number}", "price": 50000}
                for s in seats
            ],
            status=BookingStatus.PAID,
            expires_at=datetime.now() + timedelta(minutes=10),
            paid_at=datetime.now(),
        )
        db_session.add(booking)
        db_session.flush()
        tickets = []
        for s in seats:
            t = Ticket(
                booking_id=booking.id,
                seat_id=s.id,
                price=50000,
                secret_code=secrets.token_urlsafe(16),
                status=TicketStatus.ACTIVE,
            )
            db_session.add(t)
            tickets.append(t)
        db_session.commit()
        return booking, tickets

    return create

class TestCancelTicket:
    CANCEL_URL = "/api/tickets/{ticket_id}/cancel"

    def test_cancel_requires_login(self, anon_client):
        resp = anon_client.put(self.CANCEL_URL.format(ticket_id=1))
        assert resp.status_code == 401

    def test_cannot_cancel_other_users_ticket(
        self, auth_client_user2, test_data, create_paid_booking, user_data
    ):
        seats = test_data["seats"]
        far_showtime = test_data["far_future_showtime"]

        _, tickets = create_paid_booking(
            seat_ids=[seats[0].id],
            showtime=far_showtime,
            user=user_data["user"],
        )

        resp = auth_client_user2.put(self.CANCEL_URL.format(ticket_id=tickets[0].id))
        assert resp.status_code == 403

    def test_cancel_nonexistent_ticket(self, auth_client):
        resp = auth_client.put(self.CANCEL_URL.format(ticket_id=99999))
        assert resp.status_code == 404

    def test_cancel_ticket_success(self, auth_client, test_data, create_paid_booking, db_session, user_data):
        seats = test_data["seats"]
        far_showtime = test_data["far_future_showtime"]

        _, tickets = create_paid_booking(
            seat_ids=[seats[0].id],
            showtime=far_showtime,
            user=user_data["user"],
        )

        resp = auth_client.put(self.CANCEL_URL.format(ticket_id=tickets[0].id))
        assert resp.status_code == 200

        updated = Ticket.query.get(tickets[0].id)
        assert updated.status == TicketStatus.CANCELLED

    def test_cannot_cancel_less_than_2_hours_before(
        self, auth_client, test_data, create_paid_booking, user_data
    ):
        seats = test_data["seats"]
        close_showtime = test_data["close_showtime"]

        _, tickets = create_paid_booking(
            seat_ids=[seats[0].id],
            showtime=close_showtime,
            user=user_data["user"],
        )

        resp = auth_client.put(self.CANCEL_URL.format(ticket_id=tickets[0].id))
        assert resp.status_code == 400

    def test_cancel_at_exactly_2_hours_boundary(
        self, auth_client, test_data, db_session, create_paid_booking, user_data
    ):
        seats = test_data["seats"]
        movie = test_data["movie"]
        room = test_data["room"]

        boundary_showtime = Showtime(
            movie_id=movie.id,
            room_id=room.id,
            start_at=datetime.now() + timedelta(hours=2, seconds=5),
            end_at=datetime.now() + timedelta(hours=4),
        )
        db_session.add(boundary_showtime)
        db_session.flush()

        _, tickets = create_paid_booking(
            seat_ids=[seats[1].id],
            showtime=boundary_showtime,
            user=user_data["user"],
        )

        resp = auth_client.put(self.CANCEL_URL.format(ticket_id=tickets[0].id))
        assert resp.status_code == 200, (
            f"Expected 200 at boundary (>= 2h), got {resp.status_code}: {resp.get_json()}"
        )

    def test_cannot_cancel_checked_in_ticket(
        self, auth_client, test_data, create_paid_booking, db_session, user_data
    ):
        seats = test_data["seats"]
        far_showtime = test_data["far_future_showtime"]

        _, tickets = create_paid_booking(
            seat_ids=[seats[0].id],
            showtime=far_showtime,
            user=user_data["user"],
        )

        ticket = tickets[0]
        ticket.status = TicketStatus.USED
        ticket.checkin_at = datetime.now()
        db_session.commit()

        resp = auth_client.put(self.CANCEL_URL.format(ticket_id=ticket.id))
        assert resp.status_code == 400