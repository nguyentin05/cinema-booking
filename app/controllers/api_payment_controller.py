from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest

from app.decorators import api_login_required
from app.services.payment_service import PaymentServiceFactory, StripePaymentService

api_payment = Blueprint("api_payment", __name__)


@api_payment.route('/', methods=['POST'])
@api_login_required
def pay():
    data = request.get_json()
    method = data.get('method')
    booking_id = data.get('booking_id')

    service = PaymentServiceFactory.get(method)
    if not service:
        raise BadRequest("method must be: 'stripe' or 'momo'")

    res = {}
    if method == 'stripe':
        return_url = data.get('return_url', request.host_url)
        res = service.process_payment(booking_id, return_url=return_url)
        
    res['method'] = method
    return jsonify(res), 200


@api_payment.route('/stripe/callback', methods=['POST'])
def stripe_callback():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")
    webhook_secret = current_app.config['STRIPE_WEBHOOK_SECRET']
    stripe_service = StripePaymentService()

    event = StripePaymentService.verify_event(payload, sig_header, webhook_secret)

    if event.type == 'checkout.session.completed':
        session = event.data.object
        if session.payment_status != 'paid':
            return "", 200

        data = session.metadata
        if not data:
            return "", 200

        try:
            stripe_service.handle_callback(data.booking_id, session=session)
        except SQLAlchemyError:
            return "Internal server error", 500

    return "", 200
