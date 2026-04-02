import os
import cloudinary
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-for-dev')
    MAX_BOOKING_SEAT_EACH_SHOWTIME = int(os.getenv("MAX_BOOKING_SEAT_EACH_SHOWTIME", 8))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BOOKING_EXPIRATION_TIME = int(os.getenv("BOOKING_EXPIRATION_TIME", 600))  # default 10 minutes
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

    @staticmethod
    def init_app(app):
        app.jinja_env.add_extension('jinja2.ext.do')

        cloudinary.config(
            cloud_name=os.getenv("CLOUD_NAME"),
            api_key=os.getenv("CLOUD_API_KEY"),
            api_secret=os.getenv("CLOUD_API_SECRET")
        )


class DevelopConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///cinema_dev.db")
    SQLALCHEMY_ECHO = True
    PAGE_SIZE = 4


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    PAGE_SIZE = 4


class StagingConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    PAGE_SIZE = 8


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    PAGE_SIZE = 8


configs = {
    'dev': DevelopConfig,
    'testing': TestConfig,
    'staging': StagingConfig,
    'production': ProductionConfig
}
