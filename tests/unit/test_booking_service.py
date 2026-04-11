from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from flask import current_app
from werkzeug.exceptions import Forbidden, NotFound, BadRequest, Conflict

from app import create_app
from app.models import BookingStatus
from app.services.booking_service import BookingService

app = create_app('testing_v2')


@pytest.fixture(autouse=True)
def app_ctx():
    with app.app_context():
        yield


@pytest.fixture(autouse=True)
def mock_redis(mocker):
    redis_client = MagicMock()
    redis_client.get.return_value = None
    redis_client.mget.return_value = []
    mocker.patch("app.services.booking_service.get_redis", return_value=redis_client)
    return redis_client


@pytest.fixture
def mock_db(mocker):
    db_mock = mocker.patch("app.services.booking_service.db")

    mock_query = db_mock.session.query.return_value
    mock_join = mock_query.join.return_value
    mock_filter = mock_join.filter.return_value
    mock_filter.all.return_value = []

    return db_mock


@pytest.fixture
def mock_daos(mocker):
    daos = MagicMock()
    daos.seat_dao = mocker.patch("app.services.booking_service.seat_dao")
    daos.booking_dao = mocker.patch("app.services.booking_service.booking_dao")

    daos.booking_dao.count_booked_seats_by_user.return_value = 0
    return daos


@pytest.fixture
def mock_seat_service(mocker):
    return mocker.patch("app.services.booking_service.SeatService")


@pytest.fixture
def valid_showtime():
    st = MagicMock()
    st.id = 1
    st.room_id = 10
    st.start_at = datetime.now() + timedelta(hours=2)
    return st


class TestBookingSeats:
    def test_showtime_not_found(self, mocker):
        mock_query = mocker.patch("app.services.booking_service.Showtime.query")
        mock_query.get.return_value = None

        with pytest.raises(NotFound, match="This showtime do not exist"):
            BookingService.booking_seats(1, 1, [])

    def test_has_existing_unpaid_booking(self, mocker, valid_showtime, mock_redis):
        mock_query = mocker.patch("app.services.booking_service.Showtime.query")
        mock_query.get.return_value = valid_showtime
        mock_redis.get.return_value = b"123"

        with pytest.raises(Conflict, match="existing unpaid booking_id"):
            BookingService.booking_seats(1, valid_showtime.id, [1, 2])

    def test_showtime_already_started(self, mocker, valid_showtime):
        valid_showtime.start_at = datetime.now() - timedelta(minutes=10)
        mock_query = mocker.patch("app.services.booking_service.Showtime.query")
        mock_query.get.return_value = valid_showtime

        with pytest.raises(BadRequest, match="already started"):
            BookingService.booking_seats(1, valid_showtime.id, [1, 2])

    def test_max_booking_limit_in_one_request(self, mocker, valid_showtime):
        mock_query = mocker.patch("app.services.booking_service.Showtime.query")
        mock_query.get.return_value = valid_showtime

        max_booking = current_app.config['MAX_BOOKING_SEAT_EACH_SHOWTIME']

        with pytest.raises(BadRequest, match=f"maximum of {max_booking} seats per showtime"):
            BookingService.booking_seats(1, valid_showtime.id, [i for i in range(1, max_booking + 2)])

    def test_seats_already_booked_in_db(self, mocker, valid_showtime, mock_db, mock_daos):
        mock_query = mocker.patch("app.services.booking_service.Showtime.query")
        mock_query.get.return_value = valid_showtime

        s1, s2 = MagicMock(id=1, room_id=10, seat_row="A", seat_number=1), MagicMock(id=2, room_id=10)
        mock_daos.seat_dao.get_seats_by_ids.return_value = [s1, s2]

        mock_db.session.query.return_value.join.return_value.filter.return_value.all.return_value = [(1,)]

        with pytest.raises(Conflict, match=f"already booked: {s1.seat_row}{s1.seat_number}"):
            BookingService.booking_seats(1, valid_showtime.id, [1, 2])

    def test_seats_already_held_in_redis(self, mocker, valid_showtime, mock_redis, mock_daos):
        mock_query = mocker.patch("app.services.booking_service.Showtime.query")
        mock_query.get.return_value = valid_showtime
        s1 = MagicMock(id=1, room_id=10, seat_row="A", seat_number=1)
        mock_daos.seat_dao.get_seats_by_ids.return_value = [s1]

        mock_redis.mget.return_value = [b"1"]

        with pytest.raises(Conflict, match=f"already booked: {s1.seat_row}{s1.seat_number}"):
            BookingService.booking_seats(1, valid_showtime.id, [1])

    def test_max_booking_each_showtime(self, mocker, valid_showtime, mock_daos):
        mock_query = mocker.patch("app.services.booking_service.Showtime.query")
        mock_query.get.return_value = valid_showtime

        s1 = MagicMock(id=1, room_id=10)
        mock_daos.seat_dao.get_seats_by_ids.return_value = [s1]

        max_booking = current_app.config['MAX_BOOKING_SEAT_EACH_SHOWTIME']

        mock_daos.booking_dao.count_booked_seats_by_user.return_value = max_booking

        with pytest.raises(BadRequest, match=f"maximum of {max_booking} seats"):
            BookingService.booking_seats(1, valid_showtime.id, [s1.id])

    def test_seat_not_in_room(self, mocker, valid_showtime, mock_daos):
        mock_query = mocker.patch("app.services.booking_service.Showtime.query")
        mock_query.get.return_value = valid_showtime

        s1 = MagicMock(id=1, room_id=valid_showtime.room_id + 1)
        mock_daos.seat_dao.get_seats_by_ids.return_value = [s1]

        with pytest.raises(BadRequest, match="not in this room"):
            BookingService.booking_seats(1, valid_showtime.id, [s1.id])

    def test_booking_success(self, mocker, valid_showtime, mock_daos, mock_db, mock_seat_service):
        mock_query = mocker.patch("app.services.booking_service.Showtime.query")
        mock_query.get.return_value = valid_showtime

        s1 = MagicMock(id=1, room_id=10, seat_row="A", seat_number=1)
        mock_daos.seat_dao.get_seats_by_ids.return_value = [s1]
        mock_daos.seat_dao.get_price_of_seats.return_value = {s1.id: 50000}

        booking = BookingService.booking_seats(user_id=1, showtime_id=valid_showtime.id, seat_ids=[s1.id])

        assert booking is not None
        assert booking.total_price == 50000
        assert booking.total_seats == 1

        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()
        mock_seat_service.hold_seat_for_booking.assert_called_once_with(booking)

    def test_booking_rollback(self, mocker, valid_showtime, mock_daos, mock_db, mock_seat_service):
        mock_query = mocker.patch("app.services.booking_service.Showtime.query")
        mock_query.get.return_value = valid_showtime

        s1 = MagicMock(id=1, room_id=10)
        mock_daos.seat_dao.get_seats_by_ids.return_value = [s1]
        mock_daos.seat_dao.get_price_of_seats.return_value = {s1.id: 50000}

        mock_seat_service.hold_seat_for_booking.side_effect = Exception("error")

        with pytest.raises(Exception, match="error"):
            BookingService.booking_seats(1, valid_showtime.id, [s1.id])

        mock_db.session.commit.assert_called_once()
        mock_db.session.rollback.assert_called_once()


class TestCancelBooking:
    def test_booking_not_found(self, mocker):
        mock_query = mocker.patch("app.services.booking_service.Booking.query")
        mock_query.get.return_value = None

        with pytest.raises(NotFound, match="does not exist"):
            BookingService.cancel_booking(1, 6766)

    def test_forbidden_cancel(self, mocker):
        mock_booking = MagicMock(user_id=2)
        mock_query = mocker.patch("app.services.booking_service.Booking.query")
        mock_query.get.return_value = mock_booking

        with pytest.raises(Forbidden, match="not allowed"):
            BookingService.cancel_booking(1, mock_booking.id)

    def test_cancel_success(self, mocker, mock_db, mock_seat_service):
        mock_booking = MagicMock(user_id=1, status=None)
        mock_query = mocker.patch("app.services.booking_service.Booking.query")
        mock_query.get.return_value = mock_booking

        BookingService.cancel_booking(1, mock_booking.id)

        assert mock_booking.status == BookingStatus.CANCELLED

        mock_seat_service.delete_hold_seats_of_booking.assert_called_once_with(mock_booking)
        mock_db.session.commit.assert_called_once()

    def test_cancel_rollback(self, mocker, mock_db, mock_seat_service):
        mock_booking = MagicMock(user_id=1)
        mock_query = mocker.patch("app.services.booking_service.Booking.query")
        mock_query.get.return_value = mock_booking

        mock_db.session.commit.side_effect = Exception("DB Die")

        with pytest.raises(Exception, match="DB Die"):
            BookingService.cancel_booking(1, mock_booking.id)

        mock_db.session.rollback.assert_called_once()
