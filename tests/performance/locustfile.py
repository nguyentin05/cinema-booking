from locust import HttpUser, task, between

class CinemaUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def index_page(self):
        self.client.get("/")

    @task(1)
    def get_showtimes(self):
        self.client.get("/api/showtimes/")
