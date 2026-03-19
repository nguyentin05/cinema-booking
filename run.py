import os

from app import create_app
from config import configs

if __name__ == "__main__":
    app = create_app(configs['dev'])
    with app.app_context():
        app.run(
            host=os.getenv("FLASK_HOST", "127.0.0.1"),
            debug=True
        )
