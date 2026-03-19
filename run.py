import os

from app import create_app
from config import ProductionConfig

app = create_app(ProductionConfig)

if __name__ == "__main__":
    with app.app_context():
        app.run(
            host=os.getenv("FLASK_HOST", "127.0.0.1"),
            debug=True
        )
