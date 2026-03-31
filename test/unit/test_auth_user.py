import pytest

from app import db
from app.daos import user_dao
from app.models import User


@pytest.fixture
def user_data(test_app):
    user = User(
        name='test01',
        email='ximofam@gmail.com',
        password='123456Abc'
    )

    db.session.add(user)
    db.session.commit()

    return user


def test_success(user_data):
    u = user_dao.auth_user(
        email='ximofam@gmail.com',
        password='123456Abc'
    )

    assert u.email == 'ximofam@gmail.com'


@pytest.mark.parametrize('email', [
    'ximofam@gmail.co',
    'ximofam@gmai.com',
    'ximofa@gmail.com',
    'imofam@gmail.com'
])
def test_wrong_email(user_data, email):
    password = '123456Abc'

    with pytest.raises(ValueError):
        user_dao.auth_user(email=email, password=password)


@pytest.mark.parametrize("password", [
    '123456 Abc',
    '123456abc',
    '1'
])
def test_wrong_password(user_data, password):
    email = 'ximofam@gmail.com'

    with pytest.raises(ValueError):
        user_dao.auth_user(email=email, password=password)
