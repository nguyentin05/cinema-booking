from enum import Enum as Enums

from sqlalchemy import Column, Float, Integer, ForeignKey, DateTime, Enum, String

from app.models.base_model import BaseModel


class TicketStatus(Enums):
    ACTIVE = "ACTIVE"
    USED = "USED"
    CANCELLED = "CANCELLED"


class Ticket(BaseModel):
    price = Column(Float, nullable=False)
    checkin_at = Column(DateTime, nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.ACTIVE)
    secret_code = Column(String(50), nullable=False)
