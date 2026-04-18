from locust import HttpUser, task, between
from datetime import date

class CinemaUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def index_page(self):
        self.client.get("/")

    @task(1)
    def get_showtimes(self):
        today = date.today().strftime("%Y-%m-%d")
        self.client.get(f"/api/showtimes/?movie_id=1&date={today}")