from flask import Blueprint, request, jsonify

from app.daos import movie_dao

api_movie = Blueprint('api_movie', __name__)


@api_movie.route('/')
def get_products():
    filters = request.args
    movies, paginate = movie_dao.get_movies(filters)

    res = {
        "data": [
            {
                "id": m.id,
                "title": m.title,
                "poster_url": m.poster_url,
                "duration_minutes": m.duration_minutes,
                "release_date": m.release_date,
                "status": m.status
            }
            for m in movies
        ],
        "page": paginate.page,
        "per_page": paginate.per_page,
        "total": paginate.total,
        "pages": paginate.pages
    }

    return jsonify(res), 200
