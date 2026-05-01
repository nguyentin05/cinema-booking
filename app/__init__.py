import redis
import stripe
from flask import Flask, jsonify
from flask_caching import Cache
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from config import configs

db = SQLAlchemy()
login_manager = LoginManager()
cache = Cache()


def create_app(cfg_name):
    app = Flask(__name__)

    cfg = configs[cfg_name]
    app.config.from_object(cfg)
    
    cfg.init_app(app)
    db.init_app(app=app)
    login_manager.init_app(app=app)
    if app.config.get("TESTING"):
        login_manager.session_protection = None
        
    cache.init_app(app=app)
    stripe.api_key = app.config.get("STRIPE_SECRET_KEY")
    redis_client = redis.Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        db=app.config['REDIS_DB'],
        password=app.config['REDIS_PASSWORD'],
        decode_responses=True
    )

    app.extensions['redis'] = redis_client

    register_handle_exception(app)

    from app.controllers.api_showtime_controller import api_showtime
    app.register_blueprint(api_showtime, url_prefix='/api/showtimes')

    from app.controllers.api_booking_controller import api_booking
    app.register_blueprint(api_booking, url_prefix='/api/bookings')

    from app.controllers.api_payment_controller import api_payment
    app.register_blueprint(api_payment, url_prefix='/api/payment')

    from app.controllers.api_ticket_controller import api_ticket
    app.register_blueprint(api_ticket, url_prefix='/api/tickets')

    from app.controllers.main_controller import main
    app.register_blueprint(main)

    from app.controllers.auth_controller import auth
    app.register_blueprint(auth, url_prefix='/auth')

    from app.controllers.booking_controller import booking_page
    app.register_blueprint(booking_page, url_prefix='/booking')

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app


def register_handle_exception(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(ex):
        return jsonify({
            "error": ex.description
        }), ex.code

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(ex):
        app.logger.exception(str(ex))
        return jsonify({
            "error": "Internal server error"
        }), 500

    @app.errorhandler(ValueError)
    def handle_value_error(ex):
        app.logger.exception(str(ex))
        return jsonify({
            "error": str(ex)
        }), 400
