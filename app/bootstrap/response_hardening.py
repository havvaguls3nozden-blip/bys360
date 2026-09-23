from __future__ import annotations

import os
import secrets

from flask import Flask, g, request

from app.security.headers import inject_csp_nonce_into_html
from app.security_headers import apply_default_security_headers


def register_response_hardening(app: Flask) -> None:
    """Varsayilan guvenlik basliklarini ve nonce tabanli CSP'yi uygular."""

    @app.before_request
    def prepare_csp_nonce():
        if bool(app.config.get("CSP_NONCE_ENABLED", False)):
            g.csp_nonce = secrets.token_urlsafe(16)
        else:
            g.csp_nonce = None

    @app.context_processor
    def inject_csp_nonce_context():
        return {"csp_nonce": getattr(g, "csp_nonce", None)}

    @app.after_request
    def apply_security_headers(response):
        request_id = getattr(g, "request_id", None) or request.headers.get("X-Request-ID") or request.environ.get("HTTP_X_REQUEST_ID") or os.urandom(8).hex()
        csp_nonce = getattr(g, "csp_nonce", None)
        response = inject_csp_nonce_into_html(response, csp_nonce=csp_nonce)
        # BYS360 guvenlik sertlestirmesi: X-Forwarded-Proto burada dogrudan
        # okunmaz -- istemci tarafindan sahtelenebilir. Guvenilir tek proxy
        # sinyali ProxyFix middleware'inden gecmis request.is_secure'dur
        # (bkz. app/core/reverse_proxy.py, PROXY_FIX_ENABLED). PREFERRED_URL_SCHEME
        # APP_BASE_URL'den tureyen, istemcinin etkileyemeyecegi sunucu-tarafli
        # ikinci sinyaldir; dev'de APP_BASE_URL varsayilani http oldugundan bu
        # sinyal dev'de otomatik False kalir.
        is_secure = bool(
            request.is_secure or app.config.get("PREFERRED_URL_SCHEME") == "https"
        )
        return apply_default_security_headers(
            response,
            config=app.config,
            request_id=request_id,
            is_secure=is_secure,
            csp_nonce=csp_nonce,
        )
