from flask import Blueprint, redirect, render_template

from app.daos import showtime_dao, seat_dao

booking_page = Blueprint('booking_page', __name__)


@booking_page.route('/<int:showtime_id>')
def index(showtime_id):
    showtime = showtime_dao.get_showtime(showtime_id)
    if not showtime:
        return redirect('/')

    room = showtime.room
    seats = seat_dao.get_seats_of_showtime(showtime_id)

    seating_matrix = {}
    for seat in seats:
        if seat.row not in seating_matrix:
            seating_matrix[seat.row] = []
        seating_matrix[seat.row].append(seat)

    return render_template('booking.html',
                           showtime=showtime,
                           room=room,
                           seating_matrix=seating_matrix)
