from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from werkzeug.exceptions import NotFound, Forbidden, BadRequest

from app.models import TicketStatus
from app.services.ticket_service import TicketService


@pytest.fixture(autouse=True)
def app_ctx(test_app):
    pass


@pytest.fixture
def mock_db(mocker):
    return mocker.patch("app.services.ticket_service.db")


@pytest.fixture
def mock_cache(mocker):
    return mocker.patch("app.services.ticket_service.cache")


@pytest.fixture
def mock_now(mocker):
    now = datetime(2026, 4, 12, 10, 0)
    mocker.patch("app.services.ticket_service.datetime", mocker.Mock(now=lambda: now))
    return now


class TestGetTickets:
    def test_get_tickets_empty(self, mocker):
        mock_query = mocker.patch("app.models.Booking.query")
        mock_query.options.return_value.options.return_value.filter.return_value.all.return_value = []

        res = TicketService.get_tickets_of_user(1)
        assert res == []

    def test_get_tickets_success(self, mocker):
        booking = MagicMock(id=10)
        booking.showtime.movie.title = "Batman"
        booking.showtime.room.name = "Room A"
        booking.showtime.start_at = datetime.now()
        booking.showtime.end_at = datetime.now() + timedelta(minutes=30)

        mock_query = mocker.patch("app.models.Booking.query")
        mock_query.options.return_value.filter.return_value.all.return_value = [booking]

        ticket = MagicMock(id=1, booking_id=10, price=50000)
        ticket.status = TicketStatus.ACTIVE
        ticket.seat.id = 1
        ticket.seat.seat_row = "A"
        ticket.seat.seat_number = 1
        ticket.seat.seat_type.name = "VIP"

        ticket2 = MagicMock(id=2, booking_id=10, price=50000)
        ticket2.status = TicketStatus.CANCELLED
        ticket2.seat.id = 1
        ticket2.seat.seat_row = "A"
        ticket2.seat.seat_number = 1
        ticket2.seat.seat_type.name = "VIP"

        mock_t_query = mocker.patch("app.models.Ticket.query")
        mock_t_query.options.return_value.filter.return_value.order_by.return_value = [ticket, ticket2]

        res1 = TicketService.get_tickets_of_user(1)

        mock_t_query = mocker.patch("app.models.Ticket.query")
        mock_t_query \
            .options.return_value \
            .filter.return_value \
            .filter.return_value \
            .order_by.return_value = [ticket]

        res2 = TicketService.get_tickets_of_user(1, status='ACTIVE')

        assert len(res1) == 2
        assert res1[0].showtime.movie_title == "Batman" and res1[1].showtime.movie_title == "Batman"
        assert res1[0].seat.name == "A1" and res1[1].seat.name == "A1"
        assert res1[0].seat.type == "VIP" and res1[1].seat.type == "VIP"
        assert res1[0].status == "ACTIVE" and res1[1].status == "CANCELLED"

        assert len(res2) == 1
        assert res1[0].showtime.movie_title == "Batman"
        assert res1[0].seat.name == "A1"
        assert res1[0].seat.type == "VIP"
        assert res1[0].status == "ACTIVE"


class TestCancelTicket:
    def test_cancel_not_found(self, mocker):
        mock_query = mocker.patch("app.models.Ticket.query")
        mock_query.options.return_value.filter.return_value.first.return_value = None

        with pytest.raises(NotFound):
            TicketService.cancel_ticket(1, 1)

    def test_cancel_forbidden_user(self, mocker):
        mock_ticket = MagicMock()
        mock_ticket.booking.user_id = 72

        mock_query = mocker.patch("app.models.Ticket.query")
        mock_query.options.return_value.filter.return_value.first.return_value = mock_ticket

        not_owner_of_ticket_id = mock_ticket.booking.user_id + 1
        with pytest.raises(Forbidden):
            TicketService.cancel_ticket(not_owner_of_ticket_id, 100)

    def test_cancel_already_used_or_checking(self, mocker):
        mock_ticket = MagicMock()
        mock_ticket.booking.user_id = 1
        mock_ticket.status = TicketStatus.USED

        mock_query = mocker.patch("app.models.Ticket.query")
        mock_query.options.return_value.filter.return_value.first.return_value = mock_ticket

        with pytest.raises(BadRequest, match="has been checkin"):
            TicketService.cancel_ticket(1, 1)

        mock_ticket = MagicMock()
        mock_ticket.booking.user_id = 1
        mock_ticket.status = TicketStatus.ACTIVE
        mock_ticket.checkin_at = datetime.now()

        mock_query = mocker.patch("app.models.Ticket.query")
        mock_query.options.return_value.filter.return_value.first.return_value = mock_ticket

        with pytest.raises(BadRequest, match="has been checkin"):
            TicketService.cancel_ticket(1, 1)

    def test_cancel_too_late(self, mocker, mock_now):
        mock_ticket = MagicMock()
        mock_ticket.booking.user_id = 1
        mock_ticket.status = TicketStatus.ACTIVE
        mock_ticket.checkin_at = None
        mock_ticket.booking.showtime.start_at = mock_now + timedelta(hours=1, minutes=30)

        mock_query = mocker.patch("app.models.Ticket.query")
        mock_query.options.return_value.filter.return_value.first.return_value = mock_ticket

        with pytest.raises(BadRequest, match="less than 2 hours before showtime"):
            TicketService.cancel_ticket(1, 100)

    def test_cancel_success(self, mocker, mock_now, mock_db, mock_cache):
        mock_ticket = MagicMock()
        mock_ticket.booking.user_id = 1
        mock_ticket.status = TicketStatus.ACTIVE
        mock_ticket.checkin_at = None
        mock_ticket.booking.showtime.start_at = mock_now + timedelta(hours=3)

        mock_query = mocker.patch("app.models.Ticket.query")
        mock_query.options.return_value.filter.return_value.first.return_value = mock_ticket

        TicketService.cancel_ticket(1, 100)

        assert mock_ticket.status == TicketStatus.CANCELLED
        mock_db.session.commit.assert_called_once()

        mock_cache.delete.assert_called_once_with("count_active_tickets_of_user:user_id:1")

    def test_cancel_rollback(self, mocker, mock_now, mock_db):
        mock_ticket = MagicMock()
        mock_ticket.booking.user_id = 1
        mock_ticket.booking.showtime.start_at = mock_now + timedelta(hours=5)
        mock_ticket.status = TicketStatus.ACTIVE
        mock_ticket.checkin_at = None

        mock_query = mocker.patch("app.models.Ticket.query")
        mock_query.options.return_value.filter.return_value.first.return_value = mock_ticket

        mock_db.session.commit.side_effect = Exception("DB Error")

        with pytest.raises(Exception):
            TicketService.cancel_ticket(1, 100)

        mock_db.session.rollback.assert_called_once()
