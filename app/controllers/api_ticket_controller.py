from dataclasses import asdict

from flask import Blueprint, request, jsonify
from flask_login import current_user

from app.decorators import api_login_required
from app.services.ticket_service import TicketService

api_ticket = Blueprint("api_ticket", __name__)


@api_ticket.route("/<ticket_id>/cancel", methods=["PUT"])
@api_login_required
def cancel_ticket(ticket_id):
    TicketService.cancel_ticket(current_user.id, ticket_id)
    return jsonify({"message": "Cancel ticket successfully"}), 200


@api_ticket.route("/me", methods=["GET"])
@api_login_required
def get_my_tickets():
    status = request.args.get("status")
    tickets = TicketService.get_tickets_of_user(user_id=current_user.id, status=status)

    return jsonify([asdict(t) for t in tickets]), 200
