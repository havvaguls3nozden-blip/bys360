from __future__ import annotations

from app.route_support import safe_url_for


def get_route_helper_context() -> dict[str, object]:
    return {
        "safe_url_for": safe_url_for,
    }