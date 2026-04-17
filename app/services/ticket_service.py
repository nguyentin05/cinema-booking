from datetime import datetime, timedelta

from sqlalchemy.orm import joinedload
from werkzeug.exceptions import NotFound, Forbidden, BadRequest

from app import db, cache
from app.dtos import SeatSimpleDTO, TicketDTO, ShowtimeDTO
from app.models import Ticket, TicketStatus, Booking, BookingStatus, Seat, Showtime


class TicketService:
    @staticmethod
    def get_tickets_of_user(user_id, **kwargs):
        booking_query = (
            Booking.query
            .options(
                joinedload(Booking.showtime).joinedload(Showtime.movie),
                joinedload(Booking.showtime).joinedload(Showtime.room)
            )
            .filter(
                Booking.user_id == user_id,
                Booking.status == BookingStatus.PAID
            )
        )

        booking_map = {b.id: b for b in booking_query.all()}
        if not booking_map:
            return []

        ticket_query = (
            Ticket.query
            .options(joinedload(Ticket.seat).joinedload(Seat.seat_type))
            .filter(Ticket.booking_id.in_(booking_map.keys()))
        )

        status = kwargs.get('status')
        if status:
            ticket_query = ticket_query.filter(Ticket.status == status)

        tickets = ticket_query.order_by(Ticket.id.desc())

        res = []
        for ticket in tickets:
            showtime = booking_map[ticket.booking_id].showtime

            showtime_dto = ShowtimeDTO(
                id=showtime.id,
                room_name=showtime.room.name,
                movie_title=showtime.movie.title,
                movie_poster_url=showtime.movie.poster_url,
                start_at=showtime.start_at.isoformat(),
                end_at=showtime.end_at.isoformat()
            )

            seat_dto = SeatSimpleDTO(
                id=ticket.seat.id,
                name=f"{ticket.seat.seat_row}{ticket.seat.seat_number}",
                type=ticket.seat.seat_type.name
            )

            res.append(TicketDTO(
                id=ticket.id,
                user_id=user_id,
                status=ticket.status.name,
                price=ticket.price,
                showtime=showtime_dto,
                seat=seat_dto
            ))

        return res

    @staticmethod
    def cancel_ticket(user_id, ticket_id):
        ticket = (Ticket.query
                  .options(joinedload(Ticket.booking))
                  .filter(Ticket.id == ticket_id).first())
        if not ticket:
            raise NotFound("This ticket does not exists")

        if ticket.booking.user_id != user_id:
            raise Forbidden("You are not allowed")

        if ticket.status == TicketStatus.USED or ticket.checkin_at:
            raise BadRequest("This ticket has been checkin")

        showtime = ticket.booking.showtime
        now = datetime.now()
        if showtime.start_at - timedelta(hours=2) <= now:
            raise BadRequest("Cannot cancel less than 2 hours before showtime")

        try:
            ticket.status = TicketStatus.CANCELLED
            db.session.commit()
            cache.delete(f"count_active_tickets_of_user:user_id:{user_id}")
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_qr_code_of_ticket(ticket_id):
        pass
