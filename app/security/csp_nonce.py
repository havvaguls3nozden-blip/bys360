"""BYS360 CSP nonce desteği.

Şablonlarda kullanılabilecek yardımcı: {{ csp_nonce() }}
Örnek: <script nonce="{{ csp_nonce() }}">...</script>
"""
from __future__ import annotations

import base64
import os
from typing import Any


def _feature_enabled() -> bool:
    return os.getenv("ENABLE_CSP_NONCE", "true").strip().lower() in {"1", "true", "yes", "on"}


def _nonce() -> str:
    return base64.b64encode(os.urandom(18)).decode("ascii")


def init_csp_nonce(app: Any) -> None:
    if not _feature_enabled():
        app.logger.info("BYS360 CSP nonce desteği kapalı")
        return
    try:
        from flask import g
    except Exception as exc:  # pragma: no cover
        app.logger.warning("CSP nonce için Flask context alınamadı: %s", exc)
        return

    if getattr(app, "_bys360_csp_nonce_ready", False):
        return

    @app.before_request
    def _bys360_csp_nonce_before_request():
        g.csp_nonce = _nonce()

    @app.context_processor
    def _bys360_csp_nonce_context():
        return {"csp_nonce": lambda: getattr(g, "csp_nonce", "")}

    @app.after_request
    def _bys360_csp_nonce_after_request(response):
        nonce = getattr(g, "csp_nonce", "")
        if not nonce:
            return response
        current = response.headers.get("Content-Security-Policy") or response.headers.get("Content-Security-Policy-Report-Only")
        target_header = "Content-Security-Policy"
        if current:
            updated = current
            if "script-src" in updated and f"'nonce-{nonce}'" not in updated:
                updated = updated.replace("script-src", f"script-src 'nonce-{nonce}'", 1)
            if "style-src" in updated and f"'nonce-{nonce}'" not in updated:
                updated = updated.replace("style-src", f"style-src 'nonce-{nonce}'", 1)
            response.headers[target_header] = updated
        else:
            response.headers[target_header] = (
                "default-src 'self'; "
                f"script-src 'self' 'nonce-{nonce}'; "
                f"style-src 'self' 'nonce-{nonce}' 'unsafe-inline'; "
                "img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'self'"
            )
        return response

    app._bys360_csp_nonce_ready = True
    app.logger.info("BYS360 CSP nonce desteği aktif")
