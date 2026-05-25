from locust import HttpUser, task, between

class ApiTestUser(HttpUser):
    wait_time = between(1, 2)

    @task(5)
    def get_posts(self):
        self.client.get("/posts/")

    @task(3)
    def get_single_post(self):
        self.client.get("/posts/60002")

    @task(1)
    def get_docs(self):
        self.client.get("/docs")