from flask import Blueprint, render_template

from app.daos import movie_dao

movie_page = Blueprint("movie_page", __name__)


@movie_page.route("/<int:movie_id>")
def index(movie_id):
    m = movie_dao.get_movie(movie_id)

    return render_template("movie.html", movie=m)
