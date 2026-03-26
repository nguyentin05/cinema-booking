from datetime import date

from sqlalchemy import Column, String, Text, Integer, Boolean, Date
from sqlalchemy.orm import relationship

from app import db
from app.models.base_model import BaseModel

movie_genre = db.Table(
    'movie_genres',
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id'), primary_key=True)
)


class Genre(BaseModel):
    name = Column(String(50), nullable=False, unique=True)
    movies = relationship('Movie', secondary=movie_genre, back_populates='genres')

    def __str__(self):
        return self.name


class Movie(BaseModel):
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    poster_url = Column(String(255),
                        default='https://res.cloudinary.com/datah8lgd/image/upload/v1773645075/Movie_wbafjx.jpg')
    duration_minutes = Column(Integer, nullable=False)
    release_date = Column(Date, default=date.today)
    is_active = Column(Boolean, default=True)
    genres = relationship("Genre", secondary=movie_genre, back_populates='movies')
    showtimes = relationship("Showtime", backref="movie", lazy=True)

    @property
    def status(self):
        if self.release_date <= date.today():
            return 'is_showing'

        return 'coming_soon'

    def __str__(self):
        return self.title
