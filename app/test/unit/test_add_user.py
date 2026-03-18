import pytest

from app.daos import add_user
from app.test import test_app


@pytest.fixture
def valid_user_data(test_app):
    user = {
        'name': 'Test add user',
        'email': 'ximofam@gmail.com',
        'password': '123456Abc',
        'avatar': None
    }

    return user


def test_add_user_success(valid_user_data):
    user = add_user(**valid_user_data)

    assert user.id is not None
    assert user.email == valid_user_data['email']
    assert user.name == valid_user_data['name']


def test_add_user_email_exists(valid_user_data, test_app):
    add_user(**valid_user_data)

    with pytest.raises(ValueError, match="Email already exists"):
        add_user(**valid_user_data)


@pytest.mark.parametrize("email", [
    "",
    "invalid-email",
    "test.com",
    "test@",
    "test@gmail."
])
def test_add_user_invalid_email(valid_user_data, email):
    valid_user_data["email"] = email

    with pytest.raises(ValueError):
        add_user(**valid_user_data)


@pytest.mark.parametrize("password", [
    "",  # Empty
    'Abc1',  # at least 8 chacracter
    '1' + 'a' + 'A' * 127,  # less than or equal 128 chacracter
    'ximofam1',  # no uppercase
    'XIMOFAM1',  # no lowercase
    'Ximofamm',  # no digit
    'ximofamm',  # no uppercase and digit
])
def test_add_user_invalid_password(valid_user_data, password):
    valid_user_data["password"] = password

    with pytest.raises(ValueError):
        add_user(**valid_user_data)


@pytest.mark.parametrize("name", [
    "",
    "abc",
    "a" * 51
])
def test_add_user_invalid_name(valid_user_data, name):
    valid_user_data["name"] = name

    with pytest.raises(ValueError):
        add_user(**valid_user_data)
