import os

import cloudinary


class Config:
    SECRET_KEY = 'MY_SUPER_SECRET_KEY'
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    MAX_BOOKING_SEAT_EACH_SHOWTIME = int(os.getenv("MAX_BOOKING_SEAT_EACH_SHOWTIME", 8))
    BOOKING_EXPIRATION_TIME = int(os.getenv("BOOKING_EXPIRATION_TIME", 600))  # default 10 minutes
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

    @staticmethod
    def init_app(app):
        app.jinja_env.add_extension('jinja2.ext.do')


class DevConfig(Config):
    SECRET_KEY = os.getenv('SECRET_KEY', Config.SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_ECHO = True
    PAGE_SIZE = 4

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        cloudinary.config(
            cloud_name=os.getenv("CLOUD_NAME", 'datah8lgd'),
            api_key=os.getenv("CLOUD_API_KEY", '899758535566942'),
            api_secret=os.getenv("CLOUD_API_SECRET", 'nZAFBUzO70k6dkRT5FjUTY3nGII')
        )


class ProductionConfig(Config):
    SECRET_KEY = os.getenv('SECRET_KEY', Config.SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    PAGE_SIZE = 8

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        cloudinary.config(
            cloud_name=os.getenv("CLOUD_NAME", 'datah8lgd'),
            api_key=os.getenv("CLOUD_API_KEY", '899758535566942'),
            api_secret=os.getenv("CLOUD_API_SECRET", 'nZAFBUzO70k6dkRT5FjUTY3nGII')
        )


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False


configs = {
    'dev': DevConfig,
    'production': ProductionConfig,
    'testing': TestConfig
}
