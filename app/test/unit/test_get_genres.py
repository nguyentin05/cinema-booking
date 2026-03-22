import pytest

from app import db
from app.daos import genre_dao
from app.models import Genre


@pytest.fixture
def sample_data(test_app):
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
        db.session.add(genre_obj)
        res.append(genre_obj)

    db.session.commit()

    return res


def test_success(sample_data):
    genres = genre_dao.get_genres()

    assert len(genres) == len(sample_data)
    assert all(g.id == sample_data[i].id for i, g in enumerate(genres))
