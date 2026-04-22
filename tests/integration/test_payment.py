from datetime import datetime, timedelta

import pytest

from app.exceptions import BookingHasCancelled, BookingHasExpired
from app.models import (
    Booking, BookingStatus, Movie, Seat, SeatType, Room,
    PriceRule, Showtime, Ticket, TicketStatus
)
from app.services.payment_service import PaymentService


class _ConcretePayment(PaymentService):
    def process(self, booking, **kwargs):
        pass

    def handle_expired_or_cancelled_booking(self, booking_id, **kwargs):
        pass


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

    price_rule = PriceRule(priority=0, price=50000)
    db_session.add(price_rule)

    future_showtime = Showtime(
        movie_id=movie.id,
        room_id=room.id,
        start_at=datetime.now() + timedelta(hours=24),
        end_at=datetime.now() + timedelta(hours=26),
    )
    db_session.add(future_showtime)
    db_session.add_all(seats)
    db_session.commit()

    return {
        "movie": movie,
        "room": room,
        "seats": seats,
        "seat_type": seat_type,
        "price_rule": price_rule,
        "future_showtime": future_showtime,
    }


def make_pending_booking(db_session, test_data, seats_slice, expires_at, user):
    seats = test_data["seats"][seats_slice]
    booking = Booking(
        user_id=user.id,
        showtime_id=test_data["future_showtime"].id,
        total_price=50000 * len(seats),
        total_seats=len(seats),
        seats_data=[
            {"id": s.id, "name": f"{s.seat_row}{s.seat_number}", "price": 50000}
            for s in seats
        ],
        status=BookingStatus.PENDING,
        expires_at=expires_at,
    )
    db_session.add(booking)
    db_session.commit()
    return booking, seats


class TestPayment:
    PAYMENT_URL = "/api/payment/"

    def test_payment_requires_login(self, anon_client):
        resp = anon_client.post(self.PAYMENT_URL, json={
            "method": "stripe",
            "booking_id": 1,
        })
        assert resp.status_code == 401

    def test_payment_callback_creates_tickets(self, test_data, db_session, redis_client, user_data):
        booking, seats = make_pending_booking(
            db_session, test_data,
            slice(0, 2),
            expires_at=datetime.now() + timedelta(minutes=10),
            user=user_data["user"],
        )

        user = user_data["user"]
        showtime = test_data["future_showtime"]
        redis_client.set(f"hold:user:{user.id}:booking_id", str(booking.id), ex=600)
        for s in seats:
            redis_client.set(f"hold:showtime:{showtime.id}:seat:{s.id}", str(s.id), ex=600)

        service = _ConcretePayment()
        service.handle_callback(booking.id)

        updated = Booking.query.get(booking.id)
        assert updated.status == BookingStatus.PAID

        tickets = Ticket.query.filter_by(booking_id=booking.id).all()
        assert len(tickets) == 2
        for t in tickets:
            assert t.status == TicketStatus.ACTIVE
            assert t.price == 50000

        assert redis_client.get(f"hold:user:{user.id}:booking_id") is None

    def test_tickets_are_active_after_payment(self, test_data, db_session, redis_client, user_data):
        booking, seats = make_pending_booking(
            db_session, test_data,
            slice(2, 5),
            expires_at=datetime.now() + timedelta(minutes=10),
            user=user_data["user"],
        )

        user = user_data["user"]
        redis_client.set(f"hold:user:{user.id}:booking_id", str(booking.id), ex=600)

        service = _ConcretePayment()
        service.handle_callback(booking.id)

        tickets = Ticket.query.filter_by(booking_id=booking.id).all()
        assert len(tickets) == 3
        assert all(t.status == TicketStatus.ACTIVE for t in tickets)
        assert all(t.secret_code for t in tickets)

    def test_payment_at_boundary_9m59s(self, test_data, db_session, redis_client, user_data):
        booking, seats = make_pending_booking(
            db_session, test_data,
            slice(5, 6),
            expires_at=datetime.now() + timedelta(seconds=1),
            user=user_data["user"],
        )

        user = user_data["user"]
        showtime = test_data["future_showtime"]
        redis_client.set(f"hold:user:{user.id}:booking_id", str(booking.id), ex=600)
        for s in seats:
            redis_client.set(f"hold:showtime:{showtime.id}:seat:{s.id}", str(s.id), ex=600)

        service = _ConcretePayment()
        service.handle_callback(booking.id)

        updated = Booking.query.get(booking.id)
        assert updated.status == BookingStatus.PAID

    def test_duplicate_payment_only_charges_once(self, test_data, db_session, redis_client, user_data):
        booking, seats = make_pending_booking(
            db_session, test_data,
            slice(6, 7),
            expires_at=datetime.now() + timedelta(minutes=10),
            user=user_data["user"],
        )

        user = user_data["user"]
        showtime = test_data["future_showtime"]
        redis_client.set(f"hold:user:{user.id}:booking_id", str(booking.id), ex=600)
        for s in seats:
            redis_client.set(f"hold:showtime:{showtime.id}:seat:{s.id}", str(s.id), ex=600)

        service = _ConcretePayment()

        service.handle_callback(booking.id)
        tickets_first = Ticket.query.filter_by(booking_id=booking.id).all()
        assert len(tickets_first) == 1

        service.handle_callback(booking.id)

        tickets_second = Ticket.query.filter_by(booking_id=booking.id).all()
        assert len(tickets_second) == 1

    def test_payment_fails_if_booking_expired(self, test_data, db_session, user_data):
        booking, _ = make_pending_booking(
            db_session, test_data,
            slice(0, 1),
            expires_at=datetime.now() - timedelta(minutes=1),
            user=user_data["user"],
        )

        service = _ConcretePayment()
        with pytest.raises(BookingHasExpired):
            service.process_payment(booking.id)

    def test_seat_released_after_expiry(self, test_data, redis_client, user_data):
        seats = test_data["seats"]
        showtime = test_data["future_showtime"]
        user = user_data["user"]

        redis_client.set(
            f"hold:showtime:{showtime.id}:seat:{seats[9].id}",
            str(seats[9].id),
            ex=1,
        )
        redis_client.set(f"hold:user:{user.id}:booking_id", "999", ex=1)

        import time
        time.sleep(1.1)

        assert redis_client.get(f"hold:showtime:{showtime.id}:seat:{seats[9].id}") is None
        assert redis_client.get(f"hold:user:{user.id}:booking_id") is None

    def test_payment_fails_if_booking_cancelled(self, test_data, db_session, user_data):
        seats = test_data["seats"]
        showtime = test_data["future_showtime"]
        user = user_data["user"]

        cancelled_booking = Booking(
            user_id=user.id,
            showtime_id=showtime.id,
            total_price=50000,
            total_seats=1,
            seats_data=[{"id": seats[0].id, "name": "A1", "price": 50000}],
            status=BookingStatus.CANCELLED,
            expires_at=datetime.now() + timedelta(minutes=10),
        )
        db_session.add(cancelled_booking)
        db_session.commit()

        service = _ConcretePayment()
        with pytest.raises(BookingHasCancelled):
            service.process_payment(cancelled_booking.id)