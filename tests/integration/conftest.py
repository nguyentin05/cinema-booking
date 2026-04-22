from flask import current_app

from app import login_manager

import fakeredis
import pytest
from sqlalchemy.pool import StaticPool

from app import create_app, db
from app.models import User

@pytest.fixture(scope="module")
def test_app():
    app = create_app("testing")

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }

    with app.app_context():
        yield app

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
def redis_client(test_app):
    fake_redis_client = fakeredis.FakeRedis(decode_responses=True)
    test_app.extensions['redis'] = fake_redis_client
    with test_app.app_context():
        if 'cache' in current_app.extensions:
            cache = current_app.extensions['cache']
            if hasattr(cache.cache, '_write_client'):
                cache.cache._write_client = fake_redis_client
                cache.cache._read_client = fake_redis_client
            elif hasattr(cache.cache, '_client'):
                cache.cache._client = fake_redis_client
    yield fake_redis_client
    fake_redis_client.flushall()

@pytest.fixture(autouse=True)
def disable_session_protection():
    original = login_manager.session_protection
    login_manager.session_protection = None
    yield
    login_manager.session_protection = original

@pytest.fixture
def user_data(db_session):
    user = User(email="customer@test.com", name="Customer", password="Test1234")
    user2 = User(email="other@test.com", name="Other", password="Test1234")
    db_session.add_all([user, user2])

    db_session.commit()

    return {
        "user": user,
        "user2": user2
    }

@pytest.fixture
def auth_client(test_app, user_data):
    client = test_app.test_client()
    client.post('/auth/login', data={
        "email": user_data["user"].email,
        "password": "Test1234"
    })
    return client

@pytest.fixture
def auth_client_user2(test_app, user_data):
    client = test_app.test_client()
    client.post('/auth/login', data={
        "email": user_data["user2"].email,
        "password": "Test1234"
    })
    return client

@pytest.fixture
def anon_client(test_app):
    return test_app.test_client()