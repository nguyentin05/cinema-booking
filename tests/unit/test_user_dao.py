import pytest

from app.daos import user_dao
from app.models import User


@pytest.fixture
def existing_user(db_session):
    user = User(
        name='test01',
        email='ximofam@gmail.com',
        password='123456Abc'
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def valid_user_payload():
    return {
        'name': 'Test add user',
        'email': 'ximofam2@gmail.com',
        'password': '123456Abc',
        'avatar': None
    }


class TestAddUser:

    def test_add_user_success(self, valid_user_payload, db_session):
        user = user_dao.add_user(**valid_user_payload)

        assert user.id is not None
        assert user.email == valid_user_payload['email']
        assert user.name == valid_user_payload['name']

    def test_add_user_email_exists(self, existing_user, valid_user_payload, db_session):
        valid_user_payload['email'] = existing_user.email

        with pytest.raises(ValueError, match="Email already exists"):
            user_dao.add_user(**valid_user_payload)

    @pytest.mark.parametrize("email", [
        "",
        "invalid-email",
        "tests.com",
        "tests@",
        "tests@gmail."
    ])
    def test_add_user_invalid_email(self, valid_user_payload, email):
        valid_user_payload["email"] = email

        with pytest.raises(ValueError):
            user_dao.add_user(**valid_user_payload)

    @pytest.mark.parametrize("password", [
        "",  # Empty
        'Abc1',  # less than 8 characters
        '1' + 'a' + 'A' * 127,  # greater than 128 characters
        'ximofam1',  # no uppercase
        'XIMOFAM1',  # no lowercase
        'Ximofamm',  # no digit
        'ximofamm',  # no uppercase and digit
    ])
    def test_add_user_invalid_password(self, valid_user_payload, password):
        valid_user_payload["password"] = password

        with pytest.raises(ValueError):
            user_dao.add_user(**valid_user_payload)

    @pytest.mark.parametrize("name", [
        "",
        "abc",
        "a" * 51
    ])
    def test_add_user_invalid_name(self, valid_user_payload, name):
        valid_user_payload["name"] = name

        with pytest.raises(ValueError):
            user_dao.add_user(**valid_user_payload)


class TestAuthUser:

    def test_auth_success(self, existing_user):
        u = user_dao.auth_user(
            email=existing_user.email,
            password='123456Abc'
        )

        assert u is not None
        assert u.email == existing_user.email
        assert u.id == existing_user.id

    @pytest.mark.parametrize('email', [
        'ximofam@gmail.co',
        'ximofam@gmai.com',
        'ximofa@gmail.com',
        'imofam@gmail.com'
    ])
    def test_auth_wrong_email(self, existing_user, email):
        password = '123456Abc'

        with pytest.raises(ValueError, match="Incorrect email or password"):
            user_dao.auth_user(email=email, password=password)

    @pytest.mark.parametrize("password", [
        '123456 Abc',
        '123456abc',
        '1'
    ])
    def test_auth_wrong_password(self, existing_user, password):
        email = existing_user.email

        with pytest.raises(ValueError, match="Incorrect email or password"):
            user_dao.auth_user(email=email, password=password)
