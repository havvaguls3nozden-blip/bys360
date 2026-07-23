import os
import re

from locust import HttpUser, between, task


class BYS360RemoteUser(HttpUser):
    wait_time = between(2, 6)

    def on_start(self):
        self.username = os.getenv("BYS_TEST_USER")
        self.password = os.getenv("BYS_TEST_PASS")
        if self.username and self.password:
            self.login()

    def login(self):
        response = self.client.get("/login", name="GET /login")

        csrf_match = re.search(
            r'name="csrf_token".*?value="([^"]+)"',
            response.text,
            re.DOTALL
        )

        payload = {
            "username": self.username,
            "password": self.password,
        }

        if csrf_match:
            payload["csrf_token"] = csrf_match.group(1)

        self.client.post(
            "/login",
            data=payload,
            name="POST /login",
            allow_redirects=True
        )

    @task(5)
    def dashboard(self):
        self.client.get("/dashboard", name="GET /dashboard")

    @task(4)
    def performance_dashboard(self):
        self.client.get("/performance/dashboard", name="GET /performance/dashboard")

    @task(2)
    def messages(self):
        self.client.get("/messages", name="GET /messages")

    @task(2)
    def notifications(self):
        self.client.get("/notifications", name="GET /notifications")

    @task(1)
    def support(self):
        self.client.get("/support", name="GET /support")
