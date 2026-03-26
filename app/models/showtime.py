from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models.base_model import BaseModel


class Showtime(BaseModel):
    start_at = Column(DateTime, nullable=False, default=datetime.now)
    end_at = Column(DateTime, nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    bookings = relationship("Booking", backref="showtime", lazy=True)
