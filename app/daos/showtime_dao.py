from datetime import datetime, time

from sqlalchemy.orm import joinedload

from app.models import Showtime


def get_showtime(id):
    return (
        Showtime.query
        .options(
            joinedload(Showtime.room),
            joinedload(Showtime.movie)
        )
        .filter(Showtime.id == id)
        .first()
    )


def get_showtimes(movie_id, date):
    start_of_day = datetime.combine(date, time.min)
    end_of_day = datetime.combine(date, time.max)

    return (Showtime.query.filter(
        Showtime.movie_id == movie_id,
        Showtime.start_at >= start_of_day,
        Showtime.start_at <= end_of_day)
            .order_by(Showtime.start_at)
            .all())
