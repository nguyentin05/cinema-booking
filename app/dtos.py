from dataclasses import dataclass


@dataclass
class SeatDTO:
    id: int
    row: str
    number: int
    type: str
    status: str
