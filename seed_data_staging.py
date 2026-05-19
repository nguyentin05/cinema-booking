import os
import random
import string
from datetime import datetime, timedelta

from app import create_app, db
from app.models import User, Movie, Room, Showtime, Seat, Booking, Ticket, BookingStatus, TicketStatus

def seed_data():
    app = create_app(os.environ.get('APP_ENV', 'dev'))
    with app.app_context():
        user = User.query.filter_by(email='test1@gmail.com').first()
        if not user:
            user = User(email='test1@gmail.com', name='Test User', password='Test1234!')
            db.session.add(user)
            db.session.flush()

        room = Room.query.first()
        movie = Movie.query.first()
        if not room or not movie:
            return

        start_time = datetime.now() + timedelta(hours=1, minutes=30)
        end_time = start_time + timedelta(minutes=movie.duration_minutes)

        conflict = Showtime.query.filter(
            Showtime.room_id == room.id,
            Showtime.start_at < end_time,
            Showtime.end_at > start_time
        ).first()
        if conflict:
            room = Room.query.filter(Room.id != room.id).first()
            if not room:
                return

        showtime = Showtime(
            movie_id=movie.id,
            room_id=room.id,
            start_at=start_time,
            end_at=end_time
        )
        db.session.add(showtime)
        db.session.flush()

        seat = Seat.query.filter_by(room_id=room.id).first()
        if not seat:
            return
        price = 50000.0

        booking = Booking(
            user_id=user.id,
            showtime_id=showtime.id,
            total_price=price,
            total_seats=1,
            seats_data=[{
                "seat_id": seat.id,
                "seat_row": seat.seat_row,
                "seat_number": seat.seat_number,
                "seat_type": seat.seat_type.name if seat.seat_type else "Normal"
            }],
            status=BookingStatus.PAID,
            expires_at=start_time - timedelta(minutes=5),
            paid_at=datetime.now()
        )
        db.session.add(booking)
        db.session.flush()

        secret = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        ticket = Ticket(
            booking_id=booking.id,
            seat_id=seat.id,
            price=price,
            status=TicketStatus.ACTIVE,
            secret_code=secret
        )
        db.session.add(ticket)
        db.session.commit()

if __name__ == '__main__':
    seed_data()