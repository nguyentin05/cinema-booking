from werkzeug.exceptions import BadRequest


class BookingHasExpired(BadRequest):
    description = "This booking has expired"


class BookingHasCancelled(BadRequest):
    description = "This booking has cancelled"
