import io

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


class TestGetUserById:
    def test_sucess(self, existing_user, db_session):
        user2 = User(
            name='test02',
            email='ximofam2@gmail.com',
            password='123456Abc'
        )
        db_session.add(user2)
        db_session.commit()

        user = user_dao.get_user_by_id(user2.id)

        assert user is not None
        assert user == user2

    def test_not_exists_user_with_id(self, existing_user):
        non_existent_id = existing_user.id + 72
        user = user_dao.get_user_by_id(non_existent_id)

        assert user is None


class TestAddUser:
    def test_add_user_success(self, valid_user_payload, db_session):
        user = user_dao.add_user(**valid_user_payload)

        assert user.id is not None
        assert user.email == valid_user_payload['email']
        assert user.name == valid_user_payload['name']

    def test_success_with_avatar(self, valid_user_payload, mocker, db_session):
        mock_upload = mocker.patch("app.daos.user_dao.cloudinary.uploader.upload")
        mock_upload.return_value = {
            "secure_url": "https://res.cloudinary.com/datah8lgd/image/upload/v1773747273/images_patu6r.png"}

        avatar_file = io.BytesIO(b"fake image data")
        valid_user_payload["avatar"] = avatar_file

        user = user_dao.add_user(**valid_user_payload)
        assert user.avatar == "https://res.cloudinary.com/datah8lgd/image/upload/v1773747273/images_patu6r.png"
        mock_upload.assert_called_once_with(avatar_file)

    def test_raise_db_error(self, mocker, db_session, valid_user_payload):
        mocker.patch.object(db_session, 'commit', side_effect=Exception("Database Connection Dead"))
        mock_rollback = mocker.patch.object(db_session, 'rollback')
        mock_logger = mocker.patch("app.daos.user_dao.current_app.logger.error")

        with pytest.raises(Exception, match="^Database Connection Dead$"):
            user_dao.add_user(**valid_user_payload)

        mock_rollback.assert_called_once()
        mock_logger.assert_called_once_with("Database Connection Dead")

    def test_raise_error_with_email_gt_255(self, valid_user_payload, db_session):
        valid_user_payload['email'] = "x" * 255 + "@gmail.com"

        with pytest.raises(ValueError, match="^Email must be less than or equal 255 characters$"):
            user_dao.add_user(**valid_user_payload)

    def test_add_user_email_exists(self, existing_user, valid_user_payload, db_session):
        valid_user_payload['email'] = existing_user.email

        with pytest.raises(ValueError, match="^Email already exists$"):
            user_dao.add_user(**valid_user_payload)

    @pytest.mark.parametrize("email, expected_msg", [
        ("", "Email is empty"),
        ("invalid-email", "Invalid email format"),
        ("tests.com", "Invalid email format"),
        ("tests@", "Invalid email format"),
        ("tests@gmail.", "Invalid email format")
    ])
    def test_add_user_invalid_email(self, valid_user_payload, email, expected_msg):
        valid_user_payload["email"] = email

        with pytest.raises(ValueError, match=f"^{expected_msg}$"):
            user_dao.add_user(**valid_user_payload)

    @pytest.mark.parametrize("password, expected_msg", [
        ("", "Password is empty"),  # Empty
        ('Abc1', "Password must be at least 8 characters"),  # less than 8 characters
        ('1' + 'a' + 'A' * 127, "Password must be less than or equal 128 characters"),  # greater than 128 characters
        ('ximofam1', "Password must contain at least one uppercase letter, one lowercase letter and one digit"),  # no uppercase
        ('XIMOFAM1', "Password must contain at least one uppercase letter, one lowercase letter and one digit"),  # no lowercase
        ('Ximofamm', "Password must contain at least one uppercase letter, one lowercase letter and one digit"),  # no digit
        ('ximofamm', "Password must contain at least one uppercase letter, one lowercase letter and one digit"),  # no uppercase and digit
    ])
    def test_add_user_invalid_password(self, valid_user_payload, password, expected_msg):
        valid_user_payload["password"] = password

        with pytest.raises(ValueError, match=f"^{expected_msg}$"):
            user_dao.add_user(**valid_user_payload)

    @pytest.mark.parametrize("name, expected_msg", [
        ("", "Name is empty!!!"),
        ("abc", "Name must be at least 5 characters"),
        ("a" * 51, "Name must be less than or equal 50")
    ])
    def test_add_user_invalid_name(self, valid_user_payload, name, expected_msg):
        valid_user_payload["name"] = name

        with pytest.raises(ValueError, match=f"^{expected_msg}$"):
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

        with pytest.raises(ValueError, match="^Incorrect email or password$"):
            user_dao.auth_user(email=email, password=password)

    @pytest.mark.parametrize("password", [
        '123456 Abc',
        '123456abc',
        '1'
    ])
    def test_auth_wrong_password(self, existing_user, password):
        email = existing_user.email

        with pytest.raises(ValueError, match="^Incorrect email or password$"):
            user_dao.auth_user(email=email, password=password)
