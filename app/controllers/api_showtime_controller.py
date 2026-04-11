from datetime import datetime

from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest

from app.daos import showtime_dao

api_showtime = Blueprint("api_showtime", __name__)


@api_showtime.route('/')
def get_showtimes():
    movie_id_str = request.args.get("movie_id")
    if not movie_id_str:
        raise BadRequest("Missing query param movie_id")
    try:
        movie_id = int(movie_id_str)
    except ValueError:
        raise BadRequest("movie_id must by int")

    date_str = request.args.get("date")
    if not date_str:
        raise BadRequest("Missing query param date")
    try:
        parsed_datetime = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise BadRequest("date must be YYYY-MM-DD")

    showtimes = showtime_dao.get_showtimes(movie_id, parsed_datetime.date())

    return jsonify([
        {
            "id": st.id,
            "start_at": st.start_at.isoformat(),
            "end_at": st.end_at.isoformat()
        }
        for st in showtimes
    ]), 200
