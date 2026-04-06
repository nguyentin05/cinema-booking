from datetime import datetime, timedelta

import pytest

from app.daos import booking_dao
from app.models import User, Booking, BookingStatus
from app.utils import get_redis


@pytest.fixture
def sample_data(db_session):
    user = User(name='test01', email="ximofam@gmail.com", password="Admin123")
    db_session.add(user)
    db_session.flush()

    now = datetime.now()
    cancelled_booking = Booking(
        user_id=user.id,
        showtime_id=1,
        expires_at=now,
        total_price=111222,
        total_seats=2,
        seats_data={},
        status=BookingStatus.CANCELLED
    )

    pending_booking = Booking(
        user_id=user.id,
        showtime_id=1,
        expires_at=now + timedelta(seconds=1000),
        total_price=111222,
        total_seats=2,
        seats_data={},
        status=BookingStatus.PENDING
    )
    db_session.add_all([cancelled_booking, pending_booking])
    db_session.flush()

    redis_client = get_redis()
    redis_client.set(f"hold:user:{user.id}:booking_id", pending_booking.id, ex=1000, nx=True)

    return {
        "showtime_id": 1,
        "user": user,
        "cancelled_booking": cancelled_booking,
        "pending_booking": pending_booking
    }


class TestCountBookedSeatsByUser:
    def test_return_correct_number(self, sample_data):
        user = sample_data['user']
        num = booking_dao.count_booked_seats_by_user(user_id=user.id, showtime_id=sample_data['showtime_id'])
        assert num == 4

    @pytest.mark.parametrize("user_id, showtime_id", [
        (2, 1), (1, 2)
    ])
    def test_empty_seats(self, sample_data, user_id, showtime_id):
        num = booking_dao.count_booked_seats_by_user(user_id, showtime_id)
        assert num == 0


class TestGetBookingInProgressOfUser:
    def test_return_correct(self, sample_data):
        booking = booking_dao.get_booking_in_progress_of_user(sample_data['user'].id)
        pending_booking = sample_data['pending_booking']

        assert booking is not None
        assert booking['id'] == pending_booking.id
        assert booking['total_seats'] == pending_booking.total_seats
        assert booking['total_price'] == pending_booking.total_price
        assert booking['seats_data'] == pending_booking.seats_data

    def test_fail_when_del_redis_key(self, sample_data):
        user_id = sample_data['user'].id
        booking = booking_dao.get_booking_in_progress_of_user(user_id)

        assert booking is not None

        redis_client = get_redis()
        redis_client.delete(f"hold:user:{user_id}:booking_id")
        booking = booking_dao.get_booking_in_progress_of_user(user_id)

        assert booking is None
