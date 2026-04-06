from datetime import datetime

from flask import Blueprint, request, jsonify

from app.daos import showtime_dao
from app.utils import http_bad_request

api_showtime = Blueprint("api_showtime", __name__)


@api_showtime.route('/')
def get_showtimes():
    try:
        movie_id_str = request.args.get("movie_id")
        if not movie_id_str:
            return http_bad_request(message="Missing query param movie_id")
        movie_id = int(movie_id_str)
    except ValueError:
        return http_bad_request(message="movie_id must by int")
    try:
        date_str = request.args.get("date")
        if not date_str:
            return http_bad_request(message="Missing query param date")

        parsed_datetime = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return http_bad_request(message="date must be YYYY-MM-DD")

    showtimes = showtime_dao.get_showtimes(movie_id, parsed_datetime.date())

    return jsonify([
        {
            "id": st.id,
            "start_at": st.start_at.isoformat(),
            "end_at": st.end_at.isoformat()
        }
        for st in showtimes
    ]), 200
