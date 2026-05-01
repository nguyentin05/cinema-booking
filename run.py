import os
from app import create_app
from app.admin import init_admin

cfg_name = os.environ.get('APP_ENV', 'dev')
app = create_app(cfg_name)

with app.app_context():
    init_admin(app)

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        debug=True
    )