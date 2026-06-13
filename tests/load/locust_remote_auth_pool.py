import os
import re
import itertools
from pathlib import Path
from locust import HttpUser, task, between

REDIRECT_CODES = {301, 302, 303, 307, 308}

USER_FILE = Path(__file__).with_name("bys360_test_users.txt")
COMMON_PASSWORD = os.getenv("BYS_TEST_PASS")

if not USER_FILE.exists():
    raise RuntimeError("bys360_test_users.txt bulunamadı.")

USERS = [
    line.strip().lstrip("\ufeff")
    for line in USER_FILE.read_text(encoding="utf-8-sig").splitlines()
    if line.strip()
]

if not USERS:
    raise RuntimeError("bys360_test_users.txt içinde kullanıcı yok.")

if not COMMON_PASSWORD:
    raise RuntimeError("BYS_TEST_PASS tanımlı olmalı.")

USER_CYCLE = itertools.cycle(USERS)


class BYS360PoolUser(HttpUser):
    wait_time = between(2, 6)

    def on_start(self):
        self.username = next(USER_CYCLE)
        self.password = COMMON_PASSWORD
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

            if not csrf_match:
                login_page.failure("CSRF token bulunamadı.")
                return

            csrf_token = csrf_match.group(1)
            login_page.success()

        payload = {
            "sicil_or_email": self.username,
            "password": self.password,
            "csrf_token": csrf_token,
        }

        with self.client.post(
            "/login",
            data=payload,
            name="POST /login",
            allow_redirects=False,
            catch_response=True
        ) as post_login:
            if post_login.status_code >= 400:
                post_login.failure(f"Login POST HTTP hata: {post_login.status_code} | user={self.username}")
                return

            location = post_login.headers.get("Location", "")
            if post_login.status_code in REDIRECT_CODES and location:
                post_login.success()
            else:
                post_login.failure(f"Login beklenen redirect vermedi. status={post_login.status_code} user={self.username}")
                return

        with self.client.get(
            "/dashboard",
            name="AUTH CHECK /dashboard",
            allow_redirects=False,
            catch_response=True
        ) as check:
            if check.status_code in REDIRECT_CODES:
                location = check.headers.get("Location", "")
                check.failure(f"AUTH FAILED: {self.username} dashboard yönlendirdi: {location}")
            elif check.status_code >= 400:
                check.failure(f"AUTH CHECK HTTP hata: {check.status_code} user={self.username}")
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
                if "login" in location.lower():
                    response.failure(f"SESSION LOST: {self.username} | {path} -> {location}")
                else:
                    response.success()
            elif response.status_code >= 400:
                response.failure(f"HTTP hata: {response.status_code} user={self.username}")
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
