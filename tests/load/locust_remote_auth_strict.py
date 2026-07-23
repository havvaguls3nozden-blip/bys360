import os
import re

from locust import HttpUser, between, task

REDIRECT_CODES = {301, 302, 303, 307, 308}

class BYS360StrictRemoteUser(HttpUser):
    wait_time = between(2, 6)

    def on_start(self):
        self.username = os.getenv("BYS_TEST_USER")
        self.password = os.getenv("BYS_TEST_PASS")

        if not self.username or not self.password:
            raise RuntimeError("BYS_TEST_USER ve BYS_TEST_PASS tanımlı olmalı.")

        self.login()

    def login(self):
        with self.client.get("/login", name="GET /login", catch_response=True) as login_page:
            if login_page.status_code != 200:
                login_page.failure(f"Login sayfası HTTP hata: {login_page.status_code}")
                return

            csrf_match = re.search(
                r'name="csrf_token".*?value="([^"]+)"',
                login_page.text,
                re.DOTALL
            )
            login_page.success()

        payload = {
            "sicil_or_email": self.username,
            "password": self.password,
        }

        if csrf_match:
            payload["csrf_token"] = csrf_match.group(1)

        with self.client.post(
            "/login",
            data=payload,
            name="POST /login",
            allow_redirects=False,
            catch_response=True
        ) as post_login:
            if post_login.status_code >= 400:
                post_login.failure(f"Login POST HTTP hata: {post_login.status_code}")
                return
            post_login.success()

        with self.client.get(
            "/dashboard",
            name="AUTH CHECK /dashboard",
            allow_redirects=False,
            catch_response=True
        ) as check:
            if check.status_code in REDIRECT_CODES:
                location = check.headers.get("Location", "")
                check.failure(f"AUTH FAILED: dashboard yönlendirdi: {location}")
            elif check.status_code >= 400:
                check.failure(f"AUTH CHECK HTTP hata: {check.status_code}")
            else:
                check.success()

    def auth_get(self, path, name):
        with self.client.get(
            path,
            name=name,
            allow_redirects=False,
            catch_response=True
        ) as response:
            if response.status_code in REDIRECT_CODES:
                location = response.headers.get("Location", "")
                response.failure(f"SESSION LOST veya REDIRECT: {path} yönlendirdi: {location}")
            elif response.status_code >= 400:
                response.failure(f"HTTP hata: {response.status_code}")
            else:
                response.success()

    @task(5)
    def dashboard(self):
        self.auth_get("/dashboard", "GET /dashboard")

    @task(4)
    def performance_dashboard(self):
        self.auth_get("/performance/dashboard", "GET /performance/dashboard")

    @task(2)
    def messages(self):
        self.auth_get("/messages", "GET /messages")

    @task(2)
    def notifications(self):
        self.auth_get("/notifications", "GET /notifications")

    @task(1)
    def support(self):
        self.auth_get("/support", "GET /support")
