from locust import HttpUser, task, between

class CinemaUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def index_page(self):
        self.client.get("/")

    @task(2)
    def get_movies(self):
        self.client.get("/api/movies")
