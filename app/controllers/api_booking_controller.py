from flask import Blueprint, request, jsonify
from flask_login import current_user

from app.decorators import api_login_required
from app.services.booking_service import BookingService
from app.utils import http_bad_request, http_forbidden, http_internal_server_error

api_booking = Blueprint("api_booking", __name__)


@api_booking.route('/', methods=['POST'])
@api_login_required
def booking_seats():
    data = request.get_json()
    showtime_id = data.get("showtime_id")
    seat_ids = data.get("seat_ids")
    seat_ids = [int(id) for id in seat_ids]
    user_id = current_user.id

    try:
        booking = BookingService.booking_seats(user_id, showtime_id, seat_ids)
        return jsonify({
            "id": booking.id,
            "seats_data": booking.seats_data,
            "total_seats": booking.total_seats,
            "total_price": booking.total_price,
            "expires_at": booking.expires_at.isoformat()
        }), 200
    except ValueError as ex:
        return http_bad_request(str(ex))
    except Exception as ex:
        return http_internal_server_error(ex)


@api_booking.route('/<booking_id>', methods=['DELETE'])
@api_login_required
def cancel_booking(booking_id):
    try:
        BookingService.cancel_booking(current_user.id, booking_id)
        return "", 204
    except ValueError as ex:
        return http_bad_request(str(ex))
    except PermissionError as ex:
        return http_forbidden(str(ex))
    except Exception as ex:
        return http_internal_server_error(ex)
