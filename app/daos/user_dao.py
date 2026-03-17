import re

from flask import current_app
from sqlalchemy.exc import DatabaseError
from werkzeug.exceptions import InternalServerError

from app import db
from app.models import User


def get_user_by_id(id):
    return User.query.get(id)


def add_user(email, password, name):
    _validate_name(name)
    _validate_password(password)
    _validate_email(email)

    if User.query.filter(User.email == email).first():
        raise ValueError("Email already exists")


    user = User(email=email, name=name)
    user.password = password

    db.session.add(user)
    try:
        db.session.commit()
    except DatabaseError as ex:
        db.session.rollback()
        current_app.logger.error(str(ex))
        raise InternalServerError()

    return user


def auth_user(email: str, password: str):
    _validate_email(email)

    if not password:
        raise ValueError("Incorrect email or password")


    user = User.query.filter( User.email == email).first()
    if not user or not user.verify_password(password):
        raise ValueError("Incorrect email or password")

    return user


def _validate_email(email):
    if not email:
        raise ValueError("Email is empty")

    if len(email) > 255:
        raise ValueError("Email must be less than or equal 255 characters")

    email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    if not re.match(email_regex, email):
        raise ValueError("Invalid email format")


def _validate_password(password):
    if not password:
        raise ValueError("Password is empty")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    if len(password) > 128:
        raise ValueError("Password must be less than or equal 128 characters")

    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain at least one digit")


def _validate_name(name):
    if not name:
        raise ValueError("Name is empty!!!")

    len_name = len(name)
    if len_name < 5:
        raise ValueError("Name must be at least 5 characters")

    if len_name > 50:
        raise ValueError("Name must be less than or equal 50")

