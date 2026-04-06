from datetime import datetime, date

import pytest

from app.daos import showtime_dao
from app.models import Movie, Room, Showtime


@pytest.fixture
def sample_data(db_session):
    movie = Movie(title="Avengers", duration_minutes=120)
    room = Room(name="Room 1", total_seats=50)
    showtime = Showtime(
        movie=movie,
        room=room,
        start_at=datetime(2025, 6, 1, 10, 0),
        end_at=datetime(2025, 6, 1, 12, 0)
    )
    db_session.add_all([movie, room, showtime])
    db_session.commit()


def test_get_showtime(sample_data):
    result = showtime_dao.get_showtime(1)
    assert result is not None
    assert result.movie.title == "Avengers"


def test_get_showtimes_by_date(sample_data):
    result = showtime_dao.get_showtimes(movie_id=1, date=date(2025, 6, 1))
    assert len(result) == 1
    assert result[0].start_at.date() == date(2025, 6, 1)


def test_get_showtimes_wrong_date(sample_data):
    result = showtime_dao.get_showtimes(movie_id=1, date=date(2025, 12, 31))
    assert result == []
