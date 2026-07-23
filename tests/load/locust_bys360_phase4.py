
from __future__ import annotations

import os
import random
import re

from locust import HttpUser, between, task

"""BYS360 Faz 4 Locust yük testi.

Örnek:
    locust -f tests/load/locust_bys360_phase4.py --host=http://127.0.0.1:8000

Hedef:
    150 eşzamanlı kullanıcı
    Ortalama yanıt < 500ms
    95p < 1500ms
"""


class BYS360User(HttpUser):
    wait_time = between(1, 4)

    def on_start(self):
        username = os.getenv("BYS360_LOAD_USERNAME", "")
        password = os.getenv("BYS360_LOAD_PASSWORD", "")
        if not username or not password:
            return
        response = self.client.get("/login", name="GET /login")
        token = ""
        match = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)', response.text or "")
        if match:
            token = match.group(1)
        payload = {"username": username, "password": password}
        if token:
            payload["csrf_token"] = token
        self.client.post("/login", data=payload, name="POST /login", catch_response=True)

    @task(8)
    def health(self):
        self.client.get("/health", name="GET /health")

    @task(6)
    def unread_count(self):
        self.client.get("/notifications/unread-count", name="GET /notifications/unread-count")

    @task(4)
    def dashboard(self):
        self.client.get("/dashboard", name="GET /dashboard")

    @task(3)
    def performance_dashboard(self):
        self.client.get("/performance/dashboard", name="GET /performance/dashboard")

    @task(2)
    def performance_reports(self):
        self.client.get("/performance/reports", name="GET /performance/reports")

    @task(1)
    def mixed_navigation(self):
        endpoints = [
            "/notifications",
            "/profile",
            "/performance/process-tracking",
            "/performance/process-reports",
            "/support",
        ]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, name=f"GET {endpoint}")
