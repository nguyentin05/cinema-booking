from app import create_app
from config import ProductionConfig

app = create_app(ProductionConfig)

if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)
