from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
import stripe
from werkzeug.exceptions import BadRequest

from app.exceptions import BookingHasExpired, BookingHasCancelled
from app.models import BookingStatus, Booking
from app.services.payment_service import PaymentService, StripePaymentService, PaymentServiceFactory


@pytest.fixture(autouse=True)
def app_ctx(init_db):
    pass


@pytest.fixture
def mock_db(mocker):
    return mocker.patch("app.services.payment_service.db")


@pytest.fixture
def mock_cache(mocker):
    return mocker.patch("app.services.payment_service.cache")


@pytest.fixture
def mock_seat_service(mocker):
    return mocker.patch("app.services.payment_service.SeatService")


@pytest.fixture
def mock_stripe(mocker):
    return mocker.patch("app.services.payment_service.stripe")


@pytest.fixture
def sample_booking():
    booking = MagicMock(spec=Booking)
    booking.id = 1
    booking.user_id = 10
    booking.total_price = 100000
    booking.expires_at = datetime.now() + timedelta(minutes=10)
    booking.status = BookingStatus.PENDING
    booking.seats_data = [
        {'id': 1, 'name': 'A1', 'price': 50000},
        {'id': 2, 'name': 'A2', 'price': 50000}
    ]
    return booking


class TestPaymentServiceBase:
    @pytest.mark.parametrize("mock_return, expiry_delta, status, expected_exc, match_msg", [
        (None, 10, None, BadRequest, "do not exists"),
        (True, -1, BookingStatus.PENDING, BookingHasExpired, None),
        (True, 10, BookingStatus.CANCELLED, BookingHasCancelled, None),
    ])
    def test_validate_booking_exceptions(self, mocker, sample_booking, mock_return, expiry_delta, status, expected_exc,
                                         match_msg):
        mock_query = mocker.patch("app.services.payment_service.Booking.query")

        if mock_return is None:
            mock_query.get.return_value = None
        else:
            sample_booking.expires_at = datetime.now() + timedelta(minutes=expiry_delta)
            sample_booking.status = status
            mock_query.get.return_value = sample_booking

        with pytest.raises(expected_exc, match=match_msg):
            PaymentService._validate_booking(1)

    def test_handle_callback_success(self, mocker, sample_booking, mock_db, mock_cache, mock_seat_service):
        mocker.patch("app.services.payment_service.PaymentService._validate_booking", return_value=sample_booking)

        service = StripePaymentService()

        service.handle_callback(sample_booking.id)

        assert sample_booking.status == BookingStatus.PAID
        assert mock_db.session.add_all.called

        tickets_created = mock_db.session.add_all.call_args[0][0]
        assert len(tickets_created) == 2
        assert tickets_created[0].price == 50000

        mock_db.session.commit.assert_called_once()
        mock_seat_service.delete_hold_seats_of_booking.assert_called_once_with(sample_booking)
        mock_cache.delete.assert_called_once_with(f"count_active_tickets_of_user:user_id:10")

    @pytest.mark.parametrize("exception_type", [
        BookingHasExpired(),
        BookingHasCancelled(),
    ])
    def test_handle_callback_exceptions(self, mocker, exception_type, mock_db):
        mocker.patch("app.services.payment_service.PaymentService._validate_booking", side_effect=exception_type)
        service = StripePaymentService()
        service_handle_error = mocker.patch.object(service, "handle_expired_or_cancelled_booking")

        booking_id = 1
        service.handle_callback(booking_id=booking_id)

        service_handle_error.assert_called_once_with(booking_id)

        assert mock_db.session.add_all.called is False
        assert mock_db.session.commit.called is False

    def test_handle_callback_db_error(self, mocker, sample_booking, mock_db):
        mocker.patch("app.services.payment_service.PaymentService._validate_booking", return_value=sample_booking)

        mock_db.session.commit.side_effect = Exception("DB Error")

        service = StripePaymentService()
        with pytest.raises(Exception, match="DB Error"):
            service.handle_callback(1)

        mock_db.session.rollback.assert_called_once()


class TestStripePaymentService:
    def test_process_payment_success(self, mocker, sample_booking):
        mock_query = mocker.patch("app.services.payment_service.Booking.query")
        mock_query.get.return_value = sample_booking

        booking = PaymentService._validate_booking(sample_booking.id)
        assert booking.id == sample_booking.id

        mocker.patch("app.services.payment_service.StripePaymentService.process", return_value={"message": "Success"})
        service = StripePaymentService()
        res = service.process_payment(booking.id)

        assert res['message'] == 'Success'

    def test_process_creates_session(self, mock_stripe, sample_booking):
        mock_session = MagicMock()
        mock_session.client_secret = "ximofam_secret_123"
        mock_stripe.checkout.Session.create.return_value = mock_session

        service = StripePaymentService()
        result = service.process(sample_booking, return_url="http://test.com")

        assert result["client_secret"] == mock_session.client_secret
        mock_stripe.checkout.Session.create.assert_called_once()

        args = mock_stripe.checkout.Session.create.call_args[1]
        assert args['metadata']['booking_id'] == sample_booking.id

    def test_verify_event_invalid_payload(self, mock_stripe):
        mock_stripe.Webhook.construct_event.side_effect = ValueError()
        with pytest.raises(BadRequest, match="Invalid payload"):
            StripePaymentService.verify_event(b"data", "sig", "ximofam_secret")

    def test_verify_event_invalid_signature(self, mocker):
        mocker.patch(
            "app.services.payment_service.stripe.Webhook.construct_event",
            side_effect=stripe.error.SignatureVerificationError("Invalid signature", "sig"))

        with pytest.raises(BadRequest, match="Invalid signature"):
            StripePaymentService.verify_event(b"data", "sig", "ximofam_secret")

    def test_handle_expired_booking_with_refund(self, mocker, mock_stripe, mock_db):
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = BookingStatus.PENDING
        mock_booking_query = mocker.patch("app.services.payment_service.Booking.query")
        mock_stripe_session = MagicMock(payment_intent="pi_72")

        service = StripePaymentService()
        service.handle_expired_or_cancelled_booking(1, session=mock_stripe_session)

        mock_stripe.Refund.create.assert_called_once_with(payment_intent=mock_stripe_session.payment_intent)
        mock_booking_query.filter.assert_called_once()
        mock_booking_query.filter.return_value.update.assert_called_once()
        mock_db.session.commit.assert_called_once()

    @pytest.mark.parametrize("db_status, should_update", [
        (BookingStatus.CANCELLED, False),
        (BookingStatus.PENDING, True),
    ])
    def test_handle_expired_or_cancelled_fail(self, db_status, should_update, mocker, mock_stripe, mock_db):
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = db_status
        mock_booking_query = mocker.patch("app.models.Booking.query")

        service = StripePaymentService()
        mock_session = MagicMock(payment_intent="pi_123")

        service.handle_expired_or_cancelled_booking(booking_id=1, session=mock_session)

        mock_stripe.Refund.create.assert_called_once_with(payment_intent="pi_123")

        assert mock_booking_query.filter.return_value.update.called is should_update
        assert mock_db.session.commit.called is should_update

    def test_handle_expired_or_cancelled_db_error(self, mocker, mock_stripe, mock_db):
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = BookingStatus.PENDING

        mocker.patch("app.models.Booking.query")

        mock_db.session.commit.side_effect = Exception("DB Error")

        service = StripePaymentService()
        mock_session = MagicMock(payment_intent="pi_fail_123")

        with pytest.raises(Exception, match="DB Error"):
            service.handle_expired_or_cancelled_booking(booking_id=1, session=mock_session)

        mock_stripe.Refund.create.assert_called_once_with(payment_intent="pi_fail_123")
        mock_db.session.rollback.assert_called_once()


class TestPaymentServiceFactory:
    @pytest.mark.parametrize("method, expected_class, is_none", [
        ('stripe', StripePaymentService, False),
        ('momo', None, True),
        ('', None, True)
    ])
    def test_get_payment_method(self, method, expected_class, is_none):
        service = PaymentServiceFactory.get(method)
        if is_none:
            assert service is None
        else:
            assert isinstance(service, expected_class)
