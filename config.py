import os


class Config:
    SECRET_KEY = 'MY_SUPER_SECRET_KEY'
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    @staticmethod
    def init_app(app):
        pass


class ProductionConfig(Config):
    SECRET_KEY = os.getenv('SECRET_KEY', super().SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    PAGE_SIZE = 8


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
