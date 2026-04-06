from sqlalchemy import Column, Float, Integer, ForeignKey, DateTime, Boolean

from app.models.base_model import BaseModel


class Ticket(BaseModel):
    price = Column(Float, nullable=False)
    checkin_at = Column(DateTime, nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False)
    is_active = Column(Boolean, default=True)
