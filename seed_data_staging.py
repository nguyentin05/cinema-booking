import os
from datetime import datetime, timedelta

from app import create_app, db
from app.models import User, Movie, Room, Showtime, Seat, Booking

def seed_data():
    app = create_app(os.environ.get('APP_ENV', 'dev'))
    with app.app_context():
        user = User.query.filter_by(email='test1@gmail.com').first()
        if not user:
            user = User(email='test1@gmail.com', name='Test User', password='Test1234!')
            db.session.add(user)
            db.session.flush()
            print(f"Đã tạo user test1@gmail.com")

        room = Room.query.first()
        if not room:
            print("Không có phòng nào trong DB. Hãy chạy init_db trước.")
            return

        movie = Movie.query.first()
        if not movie:
            print("Không có phim nào trong DB.")
            return

        start_time = datetime.now() + timedelta(hours=1, minutes=30)
        existing = Showtime.query.filter(
            Showtime.room_id == room.id,
            Showtime.start_at < start_time + timedelta(minutes=movie.duration_minutes),
            Showtime.end_at > start_time
        ).first()
        if existing:
            print("Có suất chiếu trùng giờ, thử phòng khác...")
            room = Room.query.order_by(Room.id).offset(1).first()
            if not room:
                print("Không tìm được phòng trống.")
                return

        showtime = Showtime(
            movie_id=movie.id,
            room_id=room.id,
            start_at=start_time,
            end_at=start_time + timedelta(minutes=movie.duration_minutes)
        )
        db.session.add(showtime)
        db.session.flush()
        print(f"Đã tạo suất chiếu ID={showtime.id} lúc {start_time}")

        booked_seat_ids = [b.seat_id for b in Booking.query.filter_by(showtime_id=showtime.id).all()]
        seat = Seat.query.filter(
            Seat.room_id == room.id,
            Seat.id.notin_(booked_seat_ids) if booked_seat_ids else True
        ).first()
        if not seat:
            # Nếu phòng này hết ghế, thử phòng khác
            print("Phòng này không còn ghế trống, thử phòng khác...")
            room = Room.query.filter(Room.id != room.id).first()
            if not room:
                print("Không còn phòng nào khác.")
                return
            seat = Seat.query.filter_by(room_id=room.id).first()
            if not seat:
                print("Không tìm thấy ghế.")
                return

        booking = Booking(
            user_id=user.id,
            showtime_id=showtime.id,
            seat_id=seat.id,
            status='PAID',
            booking_date=datetime.now(),
            total_price=50000
        )
        db.session.add(booking)
        db.session.commit()
        print(f"Đã tạo vé PAID: Booking ID={booking.id}, ghế {seat.seat_row}{seat.seat_number}")
        print("Dữ liệu test đã sẵn sàng cho TC-CAN-02.")

if __name__ == '__main__':
    seed_data()