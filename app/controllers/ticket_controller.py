from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import Ticket, Booking, TicketStatus

ticket_page = Blueprint("ticket_page", __name__)


@ticket_page.route('/me')
@login_required
def my_tickets():
    tickets = (
        Ticket.query
        .join(Booking)
        .filter(Booking.user_id == current_user.id)
        .order_by(Ticket.id.desc())
        .all()
    )
    return render_template('ticket.html',
                           tickets=tickets,
                           TicketStatus=TicketStatus)
