"""Compatibility redirect helpers for retired or renamed endpoints.

This module is intentionally small. Older routes and contract tests import
``_soft_redirect`` when a legacy endpoint needs to send the user to the new
canonical endpoint without exposing a technical error page.
"""
from __future__ import annotations

from typing import Any

from flask import redirect, url_for
from werkzeug.wrappers import Response


def _soft_redirect(_legacy_reason: str, target_endpoint: str, **values: Any) -> Response:
    """Redirect a legacy/retired endpoint to a canonical endpoint."""
    return redirect(url_for(target_endpoint, **values))
