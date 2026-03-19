from datetime import date

from flask import current_app

from app.models import Movie, Genre


def get_movies(filters: dict = None):
    filters = filters or {}
    query = Movie.query

    genre_id = filters.get('genre_id')
    if genre_id:
        genre_id = int(genre_id)
        query = query.filter(
            Movie.genres.any(Genre.id == genre_id)
        )

    kw = filters.get('kw')
    if kw:
        query = query.filter(Movie.title.contains(kw))

    status = filters.get('status')
    if status:
        today = date.today()

        if status == 'is_showing':
            query = query.filter(Movie.release_date <= today)
        elif status == 'coming_soon':
            query = query.filter(Movie.release_date > today)

    query = query.filter(Movie.is_active == True)

    page = int(filters.get('page')) if filters.get('page') else 1
    page_size = current_app.config.get('PAGE_SIZE')

    paginate = query.paginate(page=page, per_page=page_size)

    return paginate.items, paginate
