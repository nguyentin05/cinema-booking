from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user

from app.decorators import api_login_required
from app.services.booking_service import BookingService

api_booking = Blueprint("api_booking", __name__)


@api_booking.route('/', methods=['POST'])
@api_login_required
def booking_seats():
    data = request.get_json()
    showtime_id = data.get("showtime_id")
    seat_ids = data.get("seat_ids")
    user_id = current_user.id

    try:
        BookingService.booking_seats(user_id, showtime_id, seat_ids)
        return jsonify({
            "message": "Your booking is successful; you have 10 minutes to pay, otherwise your ticket will be cancelled."
        }), 200
    except ValueError as ex:
        return jsonify({"error": str(ex)}), 400
    except Exception as ex:
        current_app.logger.exception(str(ex))
        return jsonify({"error": "Internal server error"}), 500
