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

    from app.controllers.main_controller import main
    app.register_blueprint(main)

    from app.controllers.auth_controller import auth
    app.register_blueprint(auth, url_prefix='/auth')

    from app.controllers.api_movie_controller import api_movie
    app.register_blueprint(api_movie, url_prefix='/api/movies')

    return app
