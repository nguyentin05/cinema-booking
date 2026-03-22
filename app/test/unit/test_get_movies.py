from datetime import timedelta, date

import pytest

from app import db
from app.daos import genre_dao, movie_dao
from app.models import Genre, Movie


@pytest.fixture
def sample_data(test_app):
    g1 = Genre(name="Action")
    g2 = Genre(name="Comedy")
    genres = [g1, g2]
    db.session.add_all(genres)
    db.session.commit()

    today = date.today()
    m1 = Movie(title="Batman", duration_minutes=100, release_date=today - timedelta(days=1), is_active=True,
               genres=[g1])
    m2 = Movie(title="Avenger Infinity War", duration_minutes=100, release_date=today + timedelta(days=5),
               is_active=True,
               genres=[g1, g2])
    m3 = Movie(title="Avenger Endgame", duration_minutes=100, release_date=today - timedelta(days=10), is_active=False,
               genres=[g2])

    movies = [m1, m2, m3]
    db.session.add_all(movies)

    db.session.commit()

    return genres, movies


def test_create_sample_data(sample_data):
    genres = genre_dao.get_genres()
    movies, paginate = movie_dao.get_movies()

    assert len(sample_data[0]) == len(genres)
    assert paginate.total == 2


def test_search_by_kw(sample_data):
    movies, _ = movie_dao.get_movies({"kw": "Avenger"})

    assert len(movies) == 1
    assert movies[0].title == "Avenger Infinity War"


def test_search_by_genre_id(sample_data):
    (g1, g2), (m1, m2, _) = sample_data

    movies, _ = movie_dao.get_movies({"genre_id": g1.id})

    assert len(movies) == 2
    assert m1.id == movies[0].id and m2.id == movies[1].id

    movies, _ = movie_dao.get_movies({"genre_id": g2.id})

    assert len(movies) == 1
    assert m2.id == movies[0].id


def test_search_by_status(sample_data):
    _, (m1, m2, _) = sample_data
    movies, _ = movie_dao.get_movies({"status": "is_showing"})

    assert len(movies) == 1
    assert m1.id == movies[0].id

    movies, _ = movie_dao.get_movies({"status": "coming_soon"})

    assert len(movies) == 1
    assert m2.id == movies[0].id
