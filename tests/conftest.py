import pytest
import os
from app import create_app, db


@pytest.fixture
def test_app():
    os.environ['APP_ENV'] = 'testing'
    app = create_app()

    with app.app_context():
        db.create_all()

        yield app

        db.drop_all()
