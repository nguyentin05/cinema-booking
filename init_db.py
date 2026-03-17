from app import create_app, db
from app.models import User, UserRole
app = create_app()


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Add admin user
        admin = User(email="admin@gmail.com",
                     name="ximofam",
                     role=UserRole.ADMIN)
        admin.password = '123456'

        db.session.add(admin)


        db.session.commit()
