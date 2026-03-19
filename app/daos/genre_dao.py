from app.models import Genre


def get_genres():
    return Genre.query.all()
