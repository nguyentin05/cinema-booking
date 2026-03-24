from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.orm import relationship

from app.models.base_model import BaseModel


class Room(BaseModel):
    name = Column(String(50), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    total_seats = Column(Integer, nullable=False, default=0)
    seats = relationship("Seat", backref="room", lazy=True)
    showtimes = relationship("Showtime", backref="room", lazy=True)

    def __str__(self):
        return self.name
