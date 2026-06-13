# -*- coding: utf-8 -*-
"""BYS360 iOS Safari PWA routes.

This module exposes root-level PWA assets so iOS/iPadOS Safari can treat
BYS360 as an installable Home Screen web app.
"""
from __future__ import annotations

from flask import Blueprint, current_app, make_response, render_template, send_from_directory

pwa_bp = Blueprint("bys360_pwa", __name__)


@pwa_bp.route("/manifest.webmanifest")
def bys360_manifest():
    """Serve the web app manifest from a stable root URL."""
    return send_from_directory(
        current_app.static_folder,
        "pwa/manifest.webmanifest",
        mimetype="application/manifest+json",
        max_age=3600,
    )


@pwa_bp.route("/sw.js")
def bys360_service_worker():
    """Serve the service worker from the site root.

    A root-level service worker is required for app-wide scope. The worker is
    deliberately conservative and does not cache authenticated HTML pages.
    """
    response = make_response(
        send_from_directory(
            current_app.static_folder,
            "pwa/bys360-sw.js",
            mimetype="application/javascript",
            max_age=0,
        )
    )
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


@pwa_bp.route("/offline")
def bys360_offline():
    """Offline fallback page with no sensitive user data."""
    return render_template("pwa/offline.html"), 503
