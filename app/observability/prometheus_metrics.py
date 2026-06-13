# -*- coding: utf-8 -*-
"""BYS360 Prometheus metrikleri.

Opsiyonel bağımlılık mantığıyla yazılmıştır: prometheus_client yoksa uygulama açılışını kırmaz.
/metrics endpoint'i yalnızca ENABLE_PROMETHEUS_METRICS=true ise aktif olur.
"""
from __future__ import annotations

import os
import time
from typing import Any


def _enabled() -> bool:
    return os.getenv("ENABLE_PROMETHEUS_METRICS", "true").strip().lower() in {"1", "true", "yes", "on"}


def init_prometheus_metrics(app: Any) -> None:
    if not _enabled():
        app.logger.info("BYS360 Prometheus metrikleri kapalı")
        return
    try:
        from flask import Response, g, request
        from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
    except Exception as exc:  # pragma: no cover
        app.logger.warning("prometheus_client bulunamadı; metrik endpoint'i pasif: %s", exc)
        return

    if getattr(app, "_bys360_prometheus_ready", False):
        return

    request_counter = Counter(
        "bys360_http_requests_total",
        "BYS360 HTTP istek sayısı",
        ["method", "endpoint", "status"],
    )
    request_latency = Histogram(
        "bys360_http_request_duration_seconds",
        "BYS360 HTTP istek süresi",
        ["method", "endpoint"],
        buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
    )
    active_requests = Gauge("bys360_http_active_requests", "BYS360 aktif istek sayısı")

    @app.before_request
    def _bys360_metrics_before_request():
        g._bys360_metrics_started_at = time.perf_counter()
        active_requests.inc()

    @app.after_request
    def _bys360_metrics_after_request(response):
        try:
            endpoint = request.endpoint or request.path
            elapsed = time.perf_counter() - getattr(g, "_bys360_metrics_started_at", time.perf_counter())
            request_counter.labels(request.method, endpoint, str(response.status_code)).inc()
            request_latency.labels(request.method, endpoint).observe(max(elapsed, 0.0))
        finally:
            active_requests.dec()
        return response

    @app.get("/metrics")
    def bys360_metrics():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    app._bys360_prometheus_ready = True
    app.logger.info("BYS360 Prometheus metrikleri aktif")
