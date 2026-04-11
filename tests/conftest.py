import fakeredis
import pytest

from app import create_app, db


@pytest.fixture
def test_app():
    app = create_app('testing')

    with app.app_context():
        yield app


@pytest.fixture
def redis_client(test_app):
    fake_redis_client = fakeredis.FakeRedis(decode_responses=True)
    test_app.extensions['redis'] = fake_redis_client

    yield fake_redis_client
    fake_redis_client.flushall()


@pytest.fixture
def init_db(test_app):
    db.create_all()
    yield db
    db.drop_all()


@pytest.fixture
def db_session(init_db):
    yield db.session

    db.session.rollback()
    db.session.remove()


@pytest.fixture
def client(test_app):
    return test_app.test_client()
