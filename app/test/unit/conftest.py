import pytest

from app import create_app, db
from config import TestConfig


@pytest.fixture
def test_app():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()

        yield app

        db.drop_all()
