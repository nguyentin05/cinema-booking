from flask import Blueprint, render_template, request

from app.daos import movie_dao

main = Blueprint('main', __name__)


@main.route('/')
def index():
    movies, paginate = movie_dao.get_movies(request.args)

    return render_template('index.html', movies=movies, paginate=paginate)
