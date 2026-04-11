from flask import Blueprint, render_template, request
from flask_login import current_user

from app import cache
from app.daos import movie_dao, booking_dao, genre_dao, ticket_dao

main = Blueprint('main', __name__)


@main.app_context_processor
def common_attributes():
    ticket_count = 0
    booking_in_progress = None

    genres = cache.get("genres")
    if not genres:
        genres = genre_dao.get_genres()
        cache.set("genres", genres, timeout=600)

    if current_user.is_authenticated:
        ticket_count_key = f"count_active_tickets_of_user:user_id:{current_user.id}"
        ticket_count = cache.get(ticket_count_key)
        if not ticket_count:
            ticket_count = ticket_dao.count_active_tickets_of_user(current_user.id)
            cache.set(ticket_count_key, ticket_count, timeout=600)

        booking_in_progress = booking_dao.get_booking_in_progress_of_user(current_user.id)

    return {
        "genres": genres,
        "ticket_count": ticket_count,
        "booking_in_progress": booking_in_progress
    }


@main.route('/')
def index():
    movies, paginate = movie_dao.get_movies(request.args)

    return render_template('index.html', movies=movies, paginate=paginate)
