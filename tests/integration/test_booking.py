import concurrent
import secrets
from datetime import datetime, timedelta

import pytest

from app.models import (
    Booking, BookingStatus, Movie, Seat, Showtime, SeatType, Room,
    PriceRule, Ticket, TicketStatus
)


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

    price_rule = PriceRule(priority=0, price=50000)

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

    db_session.add_all(seats)
    db_session.add_all([other_room_seat, price_rule, future_showtime, past_showtime, far_future_showtime])
    db_session.commit()

    return {
        "seats": seats,
        "other_room_seat": other_room_seat,
        "future_showtime": future_showtime,
        "past_showtime": past_showtime,
        "far_future_showtime": far_future_showtime,
    }


@pytest.fixture
def create_paid_booking(db_session, test_data):
    def create(seat_ids, showtime=None, user=None):
        showtime = showtime or test_data["future_showtime"]
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
        for s in seats:
            t = Ticket(
                booking_id=booking.id,
                seat_id=s.id,
                price=50000,
                secret_code=secrets.token_urlsafe(16),
                status=TicketStatus.ACTIVE,
            )
            db_session.add(t)
        db_session.commit()

    return create


class TestBookSeats:
    BOOKING_URL = "/api/bookings/"

    def test_booking_requires_login(self, anon_client, test_data):
        seats = test_data["seats"]
        showtime = test_data["future_showtime"]
        resp = anon_client.post(self.BOOKING_URL, json={
            "showtime_id": showtime.id,
            "seat_ids": [seats[0].id],
        })
        assert resp.status_code == 401

    def test_booking_seats_success(self, auth_client, test_data, redis_client):
        seats = test_data["seats"]
        showtime = test_data["future_showtime"]
        resp = auth_client.post(self.BOOKING_URL, json={
            "showtime_id": showtime.id,
            "seat_ids": [seats[0].id, seats[1].id],
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_seats"] == 2
        assert data["total_price"] == 100000
        assert "expires_at" in data
        assert "id" in data

    def test_cannot_book_already_paid_seat(self, auth_client, test_data, create_paid_booking, user_data):
        seats = test_data["seats"]
        showtime = test_data["future_showtime"]
        create_paid_booking(seat_ids=[seats[0].id], showtime=showtime, user=user_data["user2"])
        resp = auth_client.post(self.BOOKING_URL, json={
            "showtime_id": showtime.id,
            "seat_ids": [seats[0].id],
        })
        assert resp.status_code == 409

    def test_cannot_book_held_seat(self, auth_client, test_data, redis_client):
        seats = test_data["seats"]
        showtime = test_data["future_showtime"]
        redis_client.set(
            f"hold:showtime:{showtime.id}:seat:{seats[2].id}",
            seats[2].id,
            ex=600,
        )
        resp = auth_client.post(self.BOOKING_URL, json={
            "showtime_id": showtime.id,
            "seat_ids": [seats[2].id],
        })
        assert resp.status_code == 409

    def test_book_exactly_8_seats(self, auth_client, test_data):
        seats = test_data["seats"]
        showtime = test_data["future_showtime"]
        resp = auth_client.post(self.BOOKING_URL, json={
            "showtime_id": showtime.id,
            "seat_ids": [s.id for s in seats[:8]],
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_seats"] == 8

    def test_cannot_book_more_than_8_seats_at_once(self, auth_client, test_data, redis_client):
        seats = test_data["seats"]
        showtime = test_data["future_showtime"]
        resp = auth_client.post(self.BOOKING_URL, json={
            "showtime_id": showtime.id,
            "seat_ids": [s.id for s in seats[:9]],
        })
        assert resp.status_code == 400

    def test_book_8_seats_on_two_different_showtimes(self, auth_client, test_data, redis_client):
        seats = test_data["seats"]
        showtime_a = test_data["future_showtime"]
        showtime_b = test_data["far_future_showtime"]
        resp_a = auth_client.post(self.BOOKING_URL, json={
            "showtime_id": showtime_a.id,
            "seat_ids": [s.id for s in seats[:8]],
        })
        assert resp_a.status_code == 200
        redis_client.flushall()
        resp_b = auth_client.post(self.BOOKING_URL, json={
            "showtime_id": showtime_b.id,
            "seat_ids": [s.id for s in seats[:8]],
        })
        assert resp_b.status_code == 200

    def test_cannot_exceed_8_seats_across_bookings(self, auth_client, test_data, db_session, user_data):
        seats = test_data["seats"]
        showtime = test_data["future_showtime"]
        existing_booking = Booking(
            user_id=user_data["user"].id,
            showtime_id=showtime.id,
            total_price=250000,
            total_seats=5,
            seats_data=[
                {"id": s.id, "name": f"A{s.seat_number}", "price": 50000}
                for s in seats[:5]
            ],
            status=BookingStatus.PENDING,
            expires_at=datetime.now() + timedelta(minutes=10),
        )
        db_session.add(existing_booking)
        db_session.commit()
        resp = auth_client.post(self.BOOKING_URL, json={
            "showtime_id": showtime.id,
            "seat_ids": [seats[5].id, seats[6].id, seats[7].id, seats[8].id],
        })
        assert resp.status_code == 400

    def test_cannot_book_zero_or_invalid_seats(self, auth_client, test_data):
        showtime = test_data["future_showtime"]
        resp_zero = auth_client.post(self.BOOKING_URL, json={
            "showtime_id": showtime.id,
            "seat_ids": [],
        })
        assert resp_zero.status_code in (400, 422)

    def test_cannot_book_with_pending_booking(self, auth_client, test_data, redis_client, user_data):
        seats = test_data["seats"]
        showtime = test_data["future_showtime"]
        redis_client.set(f"hold:user:{user_data["user"].id}:booking_id", "999", ex=600)
        resp = auth_client.post(self.BOOKING_URL, json={
            "showtime_id": showtime.id,
            "seat_ids": [seats[0].id],
        })
        assert resp.status_code == 409

    def test_cannot_book_after_showtime_started(self, auth_client, test_data):
        seats = test_data["seats"]
        past_showtime = test_data["past_showtime"]
        resp = auth_client.post(self.BOOKING_URL, json={
            "showtime_id": past_showtime.id,
            "seat_ids": [seats[0].id],
        })
        assert resp.status_code == 400

    def test_cannot_book_seat_from_different_room(self, auth_client, test_data):
        other_seat = test_data["other_room_seat"]
        showtime = test_data["future_showtime"]
        resp = auth_client.post(self.BOOKING_URL, json={
            "showtime_id": showtime.id,
            "seat_ids": [other_seat.id],
        })
        assert resp.status_code == 400

    def test_concurrent_booking_same_seat_race_condition(self, test_app, test_data, user_data, redis_client):
        seats = test_data["seats"]
        showtime = test_data["future_showtime"]
        seat_id = seats[0].id

        def book_seat(user_email, user_password):
            with test_app.app_context():
                client = test_app.test_client()
                client.post('/auth/login', data={
                    "email": user_email,
                    "password": user_password
                })
                resp = client.post(self.BOOKING_URL, json={
                    "showtime_id": showtime.id,
                    "seat_ids": [seat_id],
                })
                return resp.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(book_seat, user_data["user"].email, "Test1234")
            future2 = executor.submit(book_seat, user_data["user2"].email, "Test1234")
            results = [future1.result(), future2.result()]

        assert 200 in results
        assert 409 in results
        assert results.count(200) == 1
        assert results.count(409) == 1
