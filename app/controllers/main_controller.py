from flask import Blueprint, render_template, request
from flask_login import current_user

from app.daos import movie_dao, booking_dao, genre_dao

main = Blueprint('main', __name__)


@main.app_context_processor
def common_attributes():
    pending_count = 0
    if current_user.is_authenticated:
        pending_count = booking_dao.count_booking_pending_of_user(current_user.id)

    return {
        "genres": genre_dao.get_genres(),
        "booking_pending_count": pending_count
    }


@main.route('/')
def index():
    movies, paginate = movie_dao.get_movies(request.args)

    return render_template('index.html', movies=movies, paginate=paginate)
