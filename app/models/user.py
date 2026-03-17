from enum import Enum as Enums

from flask_login import UserMixin
from sqlalchemy import Column, String, Boolean, Enum
from werkzeug.security import generate_password_hash, check_password_hash

from app.models.base_model import BaseModel


class UserRole(Enums):
    USER = 1
    ADMIN = 2


class User(BaseModel, UserMixin):
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)

    @property
    def is_admin(self):
        return self.user_role == UserRole.ADMIN

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
