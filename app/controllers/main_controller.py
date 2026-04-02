from flask import Blueprint, render_template, request
from flask_login import current_user

from app.daos import movie_dao, booking_dao, genre_dao, ticket_dao

main = Blueprint('main', __name__)


@main.app_context_processor
def common_attributes():
    ticket_count = 0
    booking_in_progress = "false"
    booking_id = ""
    booking_expires_at = ""

    if current_user.is_authenticated:
        ticket_count = ticket_dao.count_tickets_of_user(current_user.id)
        has_pending, b_id, b_expires = booking_dao.get_pending_booking_of_user(current_user.id)

        if has_pending:
            booking_in_progress = "true"
            booking_id = b_id
            booking_expires_at = b_expires

    return {
        "genres": genre_dao.get_genres(),
        "ticket_count": ticket_count,
        "booking_in_progress": booking_in_progress,
        "booking_id": booking_id,
        "booking_expires_at": booking_expires_at
    }


@main.route('/')
def index():
    movies, paginate = movie_dao.get_movies(request.args)

    return render_template('index.html', movies=movies, paginate=paginate)
