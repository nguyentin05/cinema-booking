import cloudinary
from flask import redirect
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from markupsafe import Markup
from wtforms import FileField

from app import db
from app.daos import seat_dao, showtime_dao
from app.models import Movie, Room, Seat, Showtime, PriceRule, SeatType


class AdminView(ModelView):
    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.is_admin


class MovieView(AdminView):
    column_list = ['id', 'title', 'poster_url', 'genres']
    form_excluded_columns = ['poster_url']
    form_extra_fields = {
        'upload_poster': FileField('Chọn file ảnh Poster (Sẽ đẩy lên Cloudinary)')
    }

    column_formatters = {
        'poster_url': lambda view, context, model, name: Markup(
            f'<img src="{model.poster_url}" style="width: 80px; border-radius: 5px;" alt="Poster">'
        ) if model.poster_url else ""
    }

    def on_model_change(self, form, model, is_created):
        file_data = form.upload_poster.data

        if file_data:
            try:
                upload_result = cloudinary.uploader.upload(file_data)
                secure_url = upload_result.get('secure_url')
                model.poster_url = secure_url
            except Exception as e:
                print(f"Lỗi upload ảnh: {e}")


class RoomView(AdminView):
    # 1. Thêm nút "Xem Sơ Đồ Ghế" vào bảng danh sách Phòng chiếu
    column_list = ('name', 'total_seats', 'is_active', 'view_seats')

    column_formatters = {
        'view_seats': lambda view, context, model, name: Markup(
            f'<a href="{view.get_url(".seating_chart", room_id=model.id)}" class="btn btn-sm btn-info">Vẽ Sơ Đồ</a>'
        )
    }

    @expose('/seating-chart/<int:room_id>')
    def seating_chart(self, room_id):
        room = self.session.query(Room).get(room_id)
        if not room:
            return self.redirect(self.get_url('.index_view'))

        seats = self.session.query(Seat).filter_by(room_id=room_id) \
            .order_by(Seat.seat_row, Seat.seat_number).all()

        seating_matrix = {}
        for seat in seats:
            row = seat.seat_row
            if row not in seating_matrix:
                seating_matrix[row] = []
            seating_matrix[row].append(seat)

        return self.render('admin/seating_chart.html',
                           room=room,
                           seating_matrix=seating_matrix)


class ShowtimeView(AdminView):
    column_list = ['id', 'movie', 'room', 'start_at', 'end_at', 'view_seats']

    column_formatters = {
        'view_seats': lambda view, context, model, name: Markup(
            f'<a href="{view.get_url(".seating_status", showtime_id=model.id)}" class="btn btn-sm btn-success">Trạng thái Ghế</a>'
        )
    }

    @expose('/seating-status/<int:showtime_id>')
    def seating_status(self, showtime_id):
        showtime = showtime_dao.get_showtime(showtime_id)
        if not showtime:
            return redirect(self.get_url('.index_view'))
        room = showtime.room
        seats = seat_dao.get_seats_of_showtime(showtime_id)

        seating_matrix = {}
        for seat in seats:
            if seat.row not in seating_matrix:
                seating_matrix[seat.row] = []
            seating_matrix[seat.row].append(seat)

        return self.render('admin/seating_status.html',
                           showtime=showtime,
                           room=room,
                           seating_matrix=seating_matrix)


class PriceRuleView(AdminView):
    column_list = ['id', 'day_of_week', 'seat_type', 'priority', 'price']


class SeatTypeView(AdminView):
    pass


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self) -> bool:
        return current_user.is_authenticated


admin = Admin(name="Movie Booking")
admin.add_view(MovieView(Movie, db.session))
admin.add_view(RoomView(Room, db.session))
admin.add_view(ShowtimeView(Showtime, db.session))
admin.add_view(PriceRuleView(PriceRule, db.session))
admin.add_view(SeatTypeView(SeatType, db.session))
admin.add_view(LogoutView(name='Logout'))


def init_admin(app):
    admin.init_app(app=app)
