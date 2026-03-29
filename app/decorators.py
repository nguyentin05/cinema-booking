from functools import wraps
from flask import jsonify, request, current_app
from flask_login import current_user


def api_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if request.method == 'OPTIONS':
            pass
        elif current_app.config.get("LOGIN_DISABLED"):
            pass
        elif not current_user.is_authenticated:
            return jsonify({
                "error": "Unauthorize"
            }), 401

        if callable(getattr(current_app, "ensure_sync", None)):
            return current_app.ensure_sync(func)(*args, **kwargs)

        return func(*args, **kwargs)

    return decorated_view
