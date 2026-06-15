from __future__ import annotations

import json
from pathlib import Path

from flask import Blueprint, Response, current_app, jsonify, make_response, render_template, render_template_string, send_from_directory

pwa_bp = Blueprint("pwa", __name__)


def _pwa_dir() -> Path:
    return Path(current_app.root_path) / "static" / "pwa"


def _send_pwa_file(filename: str, mimetype: str, cache_control: str = "no-cache, no-store, must-revalidate"):
    directory = _pwa_dir()
    response = make_response(send_from_directory(directory, filename, mimetype=mimetype))
    response.headers["Cache-Control"] = cache_control
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@pwa_bp.get("/manifest.webmanifest")
def manifest_webmanifest():
    path = _pwa_dir() / "manifest.webmanifest"
    if path.exists():
        return _send_pwa_file("manifest.webmanifest", "application/manifest+json")
    body = {
        "name": "BYS360 Bütünleşik Yönetim Sistemi",
        "short_name": "BYS360",
        "start_url": "/?source=pwa",
        "scope": "/",
        "display": "standalone",
        "background_color": "#f7f8fb",
        "theme_color": "#8B0000",
        "icons": []
    }
    return Response(json.dumps(body, ensure_ascii=False), mimetype="application/manifest+json")


@pwa_bp.get("/service-worker.js")
def service_worker_js():
    path = _pwa_dir() / "service-worker.js"
    if path.exists():
        return _send_pwa_file("service-worker.js", "application/javascript")
    return Response("self.addEventListener('fetch', function(event) {});", mimetype="application/javascript")


@pwa_bp.get("/offline")
def pwa_offline():
    try:
        return render_template("pwa/offline.html")
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/pwa/routes.py:56")
        return render_template_string("""
<!doctype html><html lang='tr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>BYS360 - Bağlantı Yok</title></head><body style='font-family:Arial,sans-serif;background:#f7f8fb;margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px'><main style='max-width:520px;background:white;border-radius:24px;padding:28px;box-shadow:0 20px 60px rgba(15,23,42,.14);border-top:8px solid #8B0000'><h1 style='color:#8B0000;margin-top:0'>Bağlantı kurulamadı</h1><p>İnternet veya kurum ağı bağlantınızı kontrol ederek tekrar deneyiniz.</p><a href='/' style='display:inline-block;margin-top:16px;background:#8B0000;color:white;text-decoration:none;padding:12px 16px;border-radius:12px;font-weight:bold'>Tekrar dene</a></main></body></html>
""")


@pwa_bp.get("/pwa/csrf-refresh")
def pwa_csrf_refresh():
    """Safari/PWA için cache'li CSRF token sonrası güvenli yenileme ucu.

    HTML cache veya service worker eski token tutarsa beyaz ekran yerine frontend bu
    uçtan yeni token alabilir. Yanıt her zaman no-store döner.
    """
    token = ""
    try:
        from flask_wtf.csrf import generate_csrf
        token = str(generate_csrf())
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/pwa/routes.py:73")
        token = ""
    response = jsonify({
        "ok": True,
        "csrf_token": token,
        "message": "Güvenlik doğrulaması yenilendi.",
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["X-BYS360-CSRF-Refresh"] = "active"
    return response
