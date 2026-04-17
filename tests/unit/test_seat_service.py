from datetime import datetime
from unittest.mock import MagicMock, call

import pytest
from werkzeug.exceptions import NotFound, Conflict

from app.services.seat_service import SeatService

NOW = datetime(2026, 4, 11, 19, 0)
SHOWTIME_ID = 1
USER_ID = 5


@pytest.fixture(autouse=True)
def app_ctx(test_app):
    pass


@pytest.fixture
def mock_showtime():
    st = MagicMock()
    st.id = SHOWTIME_ID
    st.room_id = 1
    st.start_at = NOW
    return st


@pytest.fixture
def mock_seats():
    seats = []
    for i in range(1, 4):
        s = MagicMock(id=i, seat_row="A", seat_number=i)
        s.seat_type.name = "Standard"
        seats.append(s)
    return seats


@pytest.fixture
def mocker_booked_seat_ids(mocker):
    mock_query = mocker.patch("app.services.seat_service.db.session.query")
    mock_all = mock_query.return_value.join.return_value.filter.return_value.all
    return mock_all


@pytest.fixture
def mocker_redis(mocker):
    client = MagicMock()
    mocker.patch("app.services.seat_service.get_redis", return_value=client)
    return client


@pytest.fixture
def mocker_seat_dao(mocker, mock_seats):
    dao = mocker.patch("app.services.seat_service.seat_dao")
    dao.get_seats_by_room_id.return_value = mock_seats
    dao.get_price_of_seats.return_value = {s.id: 50000 for s in mock_seats}
    return dao


@pytest.fixture
def mock_booking():
    b = MagicMock(id=1, user_id=USER_ID, showtime_id=SHOWTIME_ID)
    b.seats_data = [
        {"id": 1, "name": "A1"},
        {"id": 2, "name": "A2"}
    ]
    return b


class TestGetSeatsOfShowtime:
    def test_showtime_not_found(self, mocker):
        mock_query = mocker.patch("app.services.seat_service.Showtime.query")
        mock_query.get.return_value = None

        with pytest.raises(NotFound, match="Showtime does not exist"):
            SeatService.get_seats_of_showtime(1)

    def test_correctly_seat_status(self, mocker, mock_showtime, mocker_booked_seat_ids, mocker_redis, mocker_seat_dao):
        mock_query = mocker.patch("app.services.seat_service.Showtime.query")
        mock_query.get.return_value = mock_showtime

        mocker_booked_seat_ids.return_value = [(1,)]
        mocker_redis.scan_iter.return_value = ["hold:showtime:100:seat:2"]
        mocker_redis.mget.return_value = ["2"]

        results = SeatService.get_seats_of_showtime(SHOWTIME_ID)

        status_map = {s.id: s.status for s in results}
        assert status_map[1] == "PAID"
        assert status_map[2] == "HOLDING"
        assert status_map[3] == "AVAILABLE"

    def test_correctly_seat_price(self, mocker, mock_showtime, mocker_booked_seat_ids, mocker_redis, mocker_seat_dao):
        mock_query = mocker.patch("app.services.seat_service.Showtime.query")
        mock_query.get.return_value = mock_showtime

        mocker_booked_seat_ids.return_value = []
        mocker_redis.scan_iter.return_value = []
        mocker_redis.mget.return_value = []

        results = SeatService.get_seats_of_showtime(SHOWTIME_ID)

        assert all(r.price == 50000 for r in results)


class TestHoldSeats:
    def test_hold_seats_success(self, mocker_redis, mock_booking):
        pipe = mocker_redis.pipeline.return_value
        pipe.execute.return_value = [True, True, True]

        SeatService.hold_seat_for_booking(mock_booking)
        assert pipe.set.call_count == 3

    def test_raises_conflict_if_seat_already_held(self, mocker_redis, mock_booking):
        pipe = mocker_redis.pipeline.return_value
        pipe.execute.return_value = [False, True, True]

        with pytest.raises(Conflict, match="Seats are no longer available"):
            SeatService.hold_seat_for_booking(mock_booking)

    def test_raises_conflict_if_have_booking_in_progress(self, mocker_redis, mock_booking):
        pipe = mocker_redis.pipeline.return_value
        pipe.execute.return_value = [True, True, False]

        with pytest.raises(Conflict,
                           match="You already have a pending booking in progress. Please complete or cancel it first"):
            SeatService.hold_seat_for_booking(mock_booking)

    def test_rollback_on_failure(self, mocker_redis, mock_booking):
        pipe = mocker_redis.pipeline.return_value
        pipe.execute.return_value = [True, False, True]

        with pytest.raises(Conflict):
            SeatService.hold_seat_for_booking(mock_booking)

        mocker_redis.delete.assert_any_call(f"hold:showtime:{SHOWTIME_ID}:seat:1", f"hold:user:{USER_ID}:booking_id")


class TestDeleteHoldSeatsOfBooking:
    def test_delete_success(self, mocker_redis, mock_booking):
        SeatService.delete_hold_seats_of_booking(mock_booking)

        expected_calls = [
            call(f"hold:user:{mock_booking.user_id}:booking_id"),
            call(*[f"hold:showtime:{mock_booking.showtime_id}:seat:{seat['id']}" for seat in mock_booking.seats_data])
        ]

        mocker_redis.delete.assert_has_calls(expected_calls, any_order=False)
