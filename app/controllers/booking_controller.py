from flask import Blueprint, redirect, render_template
from flask_login import current_user, login_required

from app.daos import showtime_dao, seat_dao, ticket_dao
from app.services.seat_service import SeatService

booking_page = Blueprint('booking_page', __name__)


@booking_page.route('/<int:showtime_id>')
@login_required
def index(showtime_id):
    showtime = showtime_dao.get_showtime(showtime_id)
    if not showtime:
        return redirect('/')

    room = showtime.room
    seats = SeatService.get_seats_of_showtime(showtime_id)
    already_booked_seats = ticket_dao.count_seats_of_showtime_booked_by_user(showtime_id, current_user.id)

    seating_matrix = {}
    for seat in seats:
        if seat.row not in seating_matrix:
            seating_matrix[seat.row] = []
        seating_matrix[seat.row].append(seat)

    return render_template('booking.html',
                           showtime=showtime,
                           room=room,
                           already_booked_seats=already_booked_seats,
                           seating_matrix=seating_matrix)
