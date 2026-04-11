from dataclasses import dataclass


@dataclass
class SeatDTO:
    id: int
    row: str
    number: int
    type: str
    status: str
    price: float


@dataclass
class ShowtimeDTO:
    id: int
    movie_title: str
    movie_poster_url: str
    room_name: str
    start_at: str
    end_at: str


@dataclass
class SeatSimpleDTO:
    id: int
    name: str
    type: str


@dataclass
class TicketDTO:
    id: int
    user_id: int
    seat: SeatSimpleDTO
    showtime: ShowtimeDTO
    status: str
    price: float
