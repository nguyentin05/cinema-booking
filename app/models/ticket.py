from enum import Enum as Enums

from sqlalchemy import Column, Float, Integer, ForeignKey, Enum, DateTime

from app.models.base_model import BaseModel


class TicketStatus(Enums):
    HOLDING = 1
    PAID = 2
    CANCELLED = 3


class Ticket(BaseModel):
    status = Column(Enum(TicketStatus), default=TicketStatus.HOLDING)
    price = Column(Float, nullable=False)
    checkin_at = Column(DateTime, nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False)
