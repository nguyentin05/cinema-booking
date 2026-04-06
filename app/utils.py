import redis
from flask import current_app, jsonify


def http_bad_request(message=None, exc: Exception | None = None):
    if exc is not None:
        current_app.logger.exception(str(exc))
    error_message = message or "Bad request"
    return jsonify({"error": error_message}), 400


def http_forbidden(message=None, exc: Exception | None = None):
    if exc is not None:
        current_app.logger.exception(str(exc))
    error_message = message or "Forbidden"
    return jsonify({"error": error_message}), 403


def http_internal_server_error(ex):
    current_app.logger.exception(str(ex))
    return jsonify({"error": "Internal server error"}), 500


def get_redis() -> redis.Redis:
    return current_app.extensions['redis']
