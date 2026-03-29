from flask import Flask
from dotenv import load_dotenv
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()

load_dotenv('.env')


def create_app(cfg):
    app = Flask(__name__)

    app.config.from_object(cfg)

    cfg.init_app(app)
    db.init_app(app=app)
    login_manager.init_app(app=app)

    from app.daos import genre_dao
    @app.context_processor
    def common_attributes():
        return {
            "genres": genre_dao.get_genres()
        }

    from app.controllers.api_movie_controller import api_movie
    app.register_blueprint(api_movie, url_prefix='/api/movies')

    from app.controllers.api_showtime_controller import api_showtime
    app.register_blueprint(api_showtime, url_prefix='/api/showtimes')

    from app.controllers.api_booking_controller import api_booking
    app.register_blueprint(api_booking, url_prefix='/api/bookings')

    from app.controllers.main_controller import main
    app.register_blueprint(main)

    from app.controllers.auth_controller import auth
    app.register_blueprint(auth, url_prefix='/auth')

    from app.controllers.movie_controller import movie_page
    app.register_blueprint(movie_page, url_prefix='/movie')

    from app.controllers.booking_controller import booking_page
    app.register_blueprint(booking_page, url_prefix='/booking')

    return app
