from flask import Blueprint, request, jsonify

from app.decorators import api_login_required
from app.services.payment_service import get_payment_service
from app.utils import http_bad_request, http_internal_server_error

api_payment = Blueprint("api_payment", __name__)


@api_payment.route('/', methods=['POST'])
@api_login_required
def pay():
    data = request.get_json()
    method = data.get('method')
    booking_id = data.get('booking_id')

    service = get_payment_service(method)
    if not service:
        return http_bad_request("method must be: 'stripe' or 'momo'")

    try:
        res = service.process_payment(booking_id)
        res['method'] = method
        return jsonify(res), 200
    except ValueError as ex:
        return http_bad_request(str(ex))
    except Exception as ex:
        return http_internal_server_error(ex)
