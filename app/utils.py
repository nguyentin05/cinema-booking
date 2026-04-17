import redis
from flask import current_app


def get_redis() -> redis.Redis:
    return current_app.extensions['redis']
