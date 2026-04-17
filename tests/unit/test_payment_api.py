from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError


@pytest.fixture(autouse=True)
def app_ctx(test_app):
    pass


@pytest.fixture
def mock_user(mocker):
    user = MagicMock(id=1, is_authenticated=True)
    mocker.patch("flask_login.utils._get_user", return_value=user)
    return user


@pytest.fixture
def mock_factory(mocker):
    return mocker.patch("app.controllers.api_payment_controller.PaymentServiceFactory")


@pytest.fixture
def mock_stripe_service(mocker):
    return mocker.patch("app.controllers.api_payment_controller.StripePaymentService")


class TestPaymentApi:
    def test_unauthorize(self, client):
        res = client.post('/api/payment/', json={
            "method": 'stripe',
            "booking_id": 1
        })

        assert res.status_code == 401

    @pytest.mark.parametrize("method, booking_id, expected_status", [
        ("stripe", 100, 200),
        ("invalid_method", 100, 400),
    ])
    def test_pay_logic(self, client, mock_user, mock_factory, method, booking_id, expected_status):
        mock_service = MagicMock()
        mock_service.process_payment.return_value = {"client_secret": "test_secret"}

        if method == "stripe":
            mock_factory.get.return_value = mock_service
        else:
            mock_factory.get.return_value = None

        response = client.post("/api/payment/", json={
            "method": method,
            "booking_id": booking_id
        })

        assert response.status_code == expected_status
        if expected_status == 200:
            data = response.get_json()
            assert data["method"] == "stripe"
            assert data["client_secret"] == "test_secret"
            mock_service.process_payment.assert_called_once()


class TestStripeCallback:

    @pytest.fixture
    def mock_event(self):
        event = MagicMock()
        event.type = 'checkout.session.completed'
        event.data.object.payment_status = 'paid'
        event.data.object.metadata.booking_id = 100
        event.data.object.payment_intent = "pi_123"
        return event

    def test_callback_success(self, client, mock_stripe_service, mock_event, mocker):
        mock_stripe_service.verify_event.return_value = mock_event

        mock_instance = mock_stripe_service.return_value

        response = client.post("/api/payment/stripe/callback",
                               data="fake_payload",
                               headers={"Stripe-Signature": "fake_sig"})

        assert response.status_code == 200
        mock_instance.handle_callback.assert_called_once_with(100, session=mock_event.data.object)

    @pytest.mark.parametrize("payment_status, has_metadata, expected_called", [
        ("unpaid", True, False),
        ("paid", False, False),
    ])
    def test_callback_skip_processing(self, client, mock_stripe_service, mock_event,
                                      payment_status, has_metadata, expected_called):
        mock_event.data.object.payment_status = payment_status
        if not has_metadata:
            mock_event.data.object.metadata = None

        mock_stripe_service.verify_event.return_value = mock_event
        mock_instance = mock_stripe_service.return_value

        response = client.post("/api/payment/stripe/callback")

        assert response.status_code == 200
        assert mock_instance.handle_callback.called is expected_called

    def test_callback_db_error(self, client, mock_stripe_service, mock_event):
        mock_stripe_service.verify_event.return_value = mock_event
        mock_instance = mock_stripe_service.return_value

        mock_instance.handle_callback.side_effect = SQLAlchemyError("DB Error")

        response = client.post("/api/payment/stripe/callback")

        assert response.status_code == 500
        assert response.data.decode() == "Internal server error"
