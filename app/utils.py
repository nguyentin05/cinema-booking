import redis
from flask import current_app, jsonify


def http_bad_request(err_msg):
    return jsonify({"error": err_msg}), 400


def http_forbidden(err_msg):
    return jsonify({"error": err_msg}), 403


def http_internal_server_error(ex):
    current_app.logger.exception(str(ex))
    return jsonify({"error": "Internal server error"}), 500


def get_redis() -> redis.Redis:
    return current_app.extensions['redis']
