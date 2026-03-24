from datetime import datetime

from flask import Blueprint, request, jsonify

from app.daos import showtime_dao

api_showtime = Blueprint("api_showtime", __name__)


@api_showtime.route('/')
def get_showtimes():
    try:
        movie_id_str = request.args.get("movie_id")
        if not movie_id_str:
            return jsonify({"error": "Missing query param movie_id"}), 400

        movie_id = int(movie_id_str)
    except ValueError:
        return jsonify({"error": "movie_id must by int"}), 400

    try:
        date_str = request.args.get("date")
        if not date_str:
            return jsonify({"error": "Missing query param date"}), 400

        parsed_datetime = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "date must be YYYY-MM-DD"}), 400

    showtimes = showtime_dao.get_showtimes(movie_id, parsed_datetime.date())

    return jsonify([
        {
            "id": st.id,
            "start_at": st.start_at.strftime("%H:%M"),
            "end_at": st.end_at.strftime("%H:%M")
        }
        for st in showtimes
    ]), 200
