from app import create_app, db
from app.models import User, UserRole, Genre, Movie
from config import configs

genres = [
    {"name": "Action"},
    {"name": "Comedy"},
    {"name": "Drama"},
    {"name": "Horror"},
    {"name": "Romance"},
    {"name": "Animation"},
    {"name": "Sci-Fi"},
    {"name": "Adventure"},
    {"name": "Fantasy"},
    {"name": "Thriller"}
]

movies = [
    {
        "title": "Quỷ Nhập Tràng 2",
        "poster_url": "https://www.bhdstar.vn/wp-content/uploads/2025/02/referenceSchemeHeadOfficeallowPlaceHoldertrueheight700ldapp-24.jpg",
        "duration_minutes": 127,
        "genre_ids": [4, 10]  # Horror, Thriller
    },
    {
        "title": "Đếm Ngày Xa Mẹ",
        "poster_url": "https://iguov8nhvyobj.vcdn.cloud/media/catalog/product/cache/1/image/c5f0a1eff4c394a251036189ccddaacd/n/o/no_main-poster_final_sneak.jpg",
        "duration_minutes": 105,
        "genre_ids": [3, 5]  # Drama, Romance
    },
    {
        "title": "Cú Nhảy Kỳ Diệu",
        "poster_url": "https://iguov8nhvyobj.vcdn.cloud/media/catalog/product/cache/1/image/c5f0a1eff4c394a251036189ccddaacd/p/o/poster_cu_nhay_ky_dieu_.jpg",
        "duration_minutes": 105,
        "genre_ids": [6, 2]  # Animation, Comedy
    },
    {
        "title": "TÀI",
        "poster_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ6TTmnnCoPG20UGjnB4tVxKkq1miUDEFo1UQ&s",
        "duration_minutes": 101,
        "genre_ids": [3, 10]  # Drama, Thriller
    },
    {
        "title": "Thỏ Ơi",
        "poster_url": "https://iguov8nhvyobj.vcdn.cloud/media/catalog/product/cache/1/image/c5f0a1eff4c394a251036189ccddaacd/t/o/to_poster_official_tiectet_3x4_fa.jpg",
        "duration_minutes": 127,
        "genre_ids": [5, 2]  # Romance, Comedy
    },
    {
        "title": "Cảm Ơn Người Đã Thức Cùng Tôi",
        "poster_url": "https://iguov8nhvyobj.vcdn.cloud/media/catalog/product/cache/1/image/1800x/71252117777b696995f01934522c402d/f/i/first-look_candtct_cinema.jpg",
        "duration_minutes": 137,
        "genre_ids": [3, 5]  # Drama, Romance
    },
    {
        "title": "Tội Phạm 101",
        "poster_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRobZyPcqwH1NfltcKVKprx6vadeF5hZxW5dg&s",
        "duration_minutes": 141,
        "genre_ids": [10, 1]  # Thriller, Action
    },
    {
        "title": "Quốc Bảo",
        "poster_url": "https://upload.wikimedia.org/wikipedia/vi/thumb/2/2e/Kokuho_poster.jpg/250px-Kokuho_poster.jpg",
        "duration_minutes": 174,
        "genre_ids": [9, 8]  # Fantasy, Adventure
    },
    {
        "title": "Không Còn Chúng Ta",
        "poster_url": "https://iguov8nhvyobj.vcdn.cloud/media/catalog/product/cache/1/image/c5f0a1eff4c394a251036189ccddaacd/4/7/470x700-us.jpg",
        "duration_minutes": 115,
        "genre_ids": [5, 3]  # Romance, Drama
    },
    {
        "title": "Mùi Phở",
        "poster_url": "https://iguov8nhvyobj.vcdn.cloud/media/catalog/product/cache/3/image/1800x/71252117777b696995f01934522c402d/7/0/700x1000-mp.jpg",
        "duration_minutes": 111,
        "genre_ids": [3, 2]  # Drama, Comedy
    },
    {
        "title": "Greenland 2: Đại Di Cư",
        "poster_url": "https://iguov8nhvyobj.vcdn.cloud/media/catalog/product/cache/1/image/c5f0a1eff4c394a251036189ccddaacd/3/5/350x495-greenland.jpg",
        "duration_minutes": 98,
        "genre_ids": [1, 7, 8]  # Action, Sci-Fi, Adventure
    },
    {
        "title": "Đồi Gió Hú",
        "poster_url": "https://iguov8nhvyobj.vcdn.cloud/media/catalog/product/cache/1/image/c5f0a1eff4c394a251036189ccddaacd/p/o/poster_payoff_doi_gio_hu_6.jpg",
        "duration_minutes": 136,
        "genre_ids": [3, 5]  # Drama, Romance
    },
]

if __name__ == '__main__':
    app = create_app(configs['dev'])
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Add admin user
        admin = User(email="admin@gmail.com",
                     name="ximofam",
                     password='Admin123',
                     role=UserRole.ADMIN)

        db.session.add(admin)

        for g in genres:
            db.session.add(Genre(**g))

        db.session.commit()

        genre_map = {genre.id: genre for genre in Genre.query.all()}

        for m in movies:
            genre_ids = m.pop('genre_ids')

            movie = Movie(**m)
            movie.genres = [genre_map[g_id] for g_id in genre_ids]

            db.session.add(movie)

        db.session.commit()
