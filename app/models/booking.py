from enum import Enum as Enums

from sqlalchemy import Column, Integer, ForeignKey, Float, Enum, DateTime
from sqlalchemy.orm import relationship

from app.models.base_model import BaseModel


class BookingStatus(Enums):
    PENDING = 1
    PAID = 2
    CANCELLED = 3


class Booking(BaseModel):
    total_price = Column(Float, default=0)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    expires_at = Column(DateTime, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    tickets = relationship("Ticket", backref="booking", lazy=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    showtime_id = Column(Integer, ForeignKey("showtimes.id"), nullable=False)
