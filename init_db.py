from app import create_app, db
from app.models import User, UserRole
from config import ProductionConfig

app = create_app(ProductionConfig)

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Add admin user
        admin = User(email="admin@gmail.com",
                     name="ximofam",
                     password='Admin123',
                     role=UserRole.ADMIN)

        db.session.add(admin)

        db.session.commit()
