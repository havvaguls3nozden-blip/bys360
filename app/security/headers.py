from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from typing import Any

"""HTTP response security header yardimcilari.

BYS360 P0 guvenlik sertlestirmesi:
- script-src tarafinda unsafe-inline varsayilan kullanilmaz.
- HTML yanitlarinda inline/external script etiketlerine nonce uygulanabilir.
- CSP header'i nonce ile birlikte uretilir.
"""
logger = logging.getLogger(__name__)

DEFAULT_CSP = {
    "default-src": "'self'",
    "base-uri": "'self'",
    "form-action": "'self'",
    "frame-ancestors": "'self'",
    "img-src": "'self' data: blob: https:",
    "style-src": "'self' 'unsafe-inline' https:",
    "style-src-elem": "'self' 'unsafe-inline' https:",
    "style-src-attr": "'unsafe-inline'",
    "script-src": "'self' https:",
    "font-src": "'self' data: https:",
    "connect-src": "'self' https:",
    "frame-src": "'self' https://www.youtube.com https://www.youtube-nocookie.com https://player.vimeo.com https://www.dailymotion.com https://dailymotion.com",
    "child-src": "'self' https://www.youtube.com https://www.youtube-nocookie.com https://player.vimeo.com https://www.dailymotion.com https://dailymotion.com",
    "media-src": "'self' blob: data: https:",
    "object-src": "'none'",
}

_SCRIPT_TAG_WITHOUT_NONCE_RE = re.compile(r"<script\b(?![^>]*\bnonce=)", re.IGNORECASE)
_STYLE_TAG_WITHOUT_NONCE_RE = re.compile(r"<style\b(?![^>]*\bnonce=)", re.IGNORECASE)


def _config_get(config: Mapping[str, Any] | Any, key: str, default: Any = None) -> Any:
    if hasattr(config, 'get'):
        return config.get(key, default)
    return default


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def _remove_token(source: str, token: str) -> str:
    return ' '.join(part for part in (source or '').split() if part != token)


def build_csp_header(config: Mapping[str, Any] | Any, *, csp_nonce: str | None = None) -> str:
    raw_policy = str(_config_get(config, 'CSP_POLICY', '') or '').strip()
    if raw_policy:
        return raw_policy

    nonce_enabled = _as_bool(_config_get(config, 'CSP_NONCE_ENABLED', False))
    allow_unsafe_inline_script = _as_bool(_config_get(config, 'CSP_ALLOW_UNSAFE_INLINE_SCRIPT', False))

    directives = []
    for key, default_value in DEFAULT_CSP.items():
        value = str(_config_get(config, f"CSP_{key.replace('-', '_').upper()}", default_value) or '').strip()
        if key == 'script-src':
            if not allow_unsafe_inline_script:
                value = _remove_token(value, "'unsafe-inline'")
            if nonce_enabled and csp_nonce:
                nonce_token = f"'nonce-{csp_nonce}'"
                if nonce_token not in value.split():
                    value = (value + ' ' + nonce_token).strip()
        if value:
            directives.append(f"{key} {value}")
    return '; '.join(directives)


def inject_csp_nonce_into_html(response: Any, *, csp_nonce: str | None) -> Any:
    """HTML yanitindaki script ve style etiketlerine nonce ekler.

    Bu merkezi uygulama sayesinde 100+ template icindeki inline scriptler ve
    style bloklari tek tek elle degistirilmeden nonce tabanli CSP'ye gecilebilir.
    Script ve style etiketleri ayni istek icin ayni nonce degerini paylasir.
    """
    if not csp_nonce:
        return response
    if getattr(response, 'is_streamed', False) or getattr(response, 'direct_passthrough', False):
        return response
    content_type = response.headers.get('Content-Type', '')
    if 'text/html' not in content_type.lower():
        return response
    try:
        html = response.get_data(as_text=True)
    except Exception as exc:
        logger.exception("BYS360 critical exception captured in app/security/headers.py", exc_info=exc)
        return response
    html_lower = html.lower()
    if '<script' not in html_lower and '<style' not in html_lower:
        return response
    html = _SCRIPT_TAG_WITHOUT_NONCE_RE.sub(f'<script nonce="{csp_nonce}"', html)
    html = _STYLE_TAG_WITHOUT_NONCE_RE.sub(f'<style nonce="{csp_nonce}"', html)
    response.set_data(html)
    return response


def apply_default_security_headers(
    response: Any,
    *,
    config: Mapping[str, Any] | Any,
    request_id: str,
    is_secure: bool,
    csp_nonce: str | None = None,
) -> Any:
    response.headers.setdefault('X-Request-ID', request_id)
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Referrer-Policy', str(_config_get(config, 'REFERRER_POLICY', 'strict-origin-when-cross-origin')))
    response.headers.setdefault('Permissions-Policy', str(_config_get(config, 'PERMISSIONS_POLICY', 'geolocation=(), microphone=(), camera=()')))
    response.headers.setdefault('Cache-Control', str(_config_get(config, 'CACHE_CONTROL_POLICY', 'no-store')))
    response.headers.setdefault('Pragma', 'no-cache')
    response.headers.setdefault('Expires', '0')
    response.headers.setdefault('X-Permitted-Cross-Domain-Policies', 'none')
    response.headers.setdefault('Cross-Origin-Opener-Policy', str(_config_get(config, 'CROSS_ORIGIN_OPENER_POLICY', 'same-origin')))
    response.headers.setdefault('Cross-Origin-Resource-Policy', str(_config_get(config, 'CROSS_ORIGIN_RESOURCE_POLICY', 'same-origin')))

    if is_secure:
        response.headers.setdefault(
            'Strict-Transport-Security',
            str(_config_get(config, 'HSTS_POLICY', 'max-age=31536000; includeSubDomains')),
        )

    csp_enabled = _as_bool(_config_get(config, 'CSP_ENABLED', 'true'), True)
    if csp_enabled:
        policy_value = build_csp_header(config, csp_nonce=csp_nonce)
        if policy_value:
            report_only = _as_bool(_config_get(config, 'CSP_REPORT_ONLY', 'true'), True)
            header_name = 'Content-Security-Policy-Report-Only' if report_only else 'Content-Security-Policy'
            response.headers.setdefault(header_name, policy_value)

    return response
