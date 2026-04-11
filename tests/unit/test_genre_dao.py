import pytest

from app.daos import genre_dao
from app.models import Genre


@pytest.fixture
def sample_data(db_session):
    genres = [
        {"name": "Action"},
        {"name": "Comedy"},
        {"name": "Drama"},
        {"name": "Horror"},
        {"name": "Romance"},
        {"name": "Animation"},
        {"name": "Sci-Fi"},
        {"name": "Adventure"},
        {"name": "Fantasy"},
        {"name": "Thriller"}
    ]

    res = []

    for g in genres:
        genre_obj = Genre(**g)
        db_session.add(genre_obj)
        res.append(genre_obj)

    db_session.commit()

    return res


def test_empty_genres(db_session):
    genres = genre_dao.get_genres()
    assert len(genres) == 0


def test_success(sample_data):
    genres = genre_dao.get_genres()

    assert len(genres) == len(sample_data)
    assert all(g.id == sample_data[i].id for i, g in enumerate(genres))
