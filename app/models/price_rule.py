from enum import IntEnum

from sqlalchemy import Column, Enum, Integer, ForeignKey, Float

from app.models.base_model import BaseModel


class DayOfWeek(IntEnum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


class PriceRule(BaseModel):
    day_of_week = Column(Integer, nullable=True)
    seat_type_id = Column(Integer, ForeignKey("seat_types.id"), nullable=True)

    priority = Column(Integer, default=0)
    price = Column(Float, nullable=False)
