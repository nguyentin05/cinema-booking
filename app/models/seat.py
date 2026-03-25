from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base_model import BaseModel


class SeatType(BaseModel):
    name = Column(String(50), nullable=False, unique=True)
    seats = relationship("Seat", backref="seat_type", lazy=True)

    def __str__(self):
        return self.name


class Seat(BaseModel):
    seat_row = Column(String(10), nullable=False)
    seat_number = Column(Integer, nullable=False)
    tickets = relationship("Ticket", backref="seat", lazy=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    seat_type_id = Column(Integer, ForeignKey("seat_types.id"), nullable=False)
