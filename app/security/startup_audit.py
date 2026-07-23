from __future__ import annotations

import logging
from urllib.parse import parse_qsl, urlparse

from flask import Flask

from app.security.audit import log_runtime_security_posture

"""BYS360 baslangic guvenlik denetimleri.

Bu modul app factory icindeki production/staging guvenlik varsayilanlarini ve
runtime security posture logunu tek yerde toplar.
"""
logger = logging.getLogger(__name__)


def _postgres_sslmode_is_unsafe(db_uri: str) -> bool:
    parsed = urlparse((db_uri or '').strip())
    if not (parsed.scheme or '').lower().startswith('postgres'):
        return False
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    return (query.get('sslmode') or '').strip().lower() == 'disable'


def _looks_like_sentry_placeholder(dsn: str) -> bool:
    lowered = (dsn or '').strip().lower()
    if not lowered:
        return False
    return any(token in lowered for token in ('https://...@sentry.io/', 'sentry.io/...', 'your-public-key', 'project-id', 'change-me'))


def validate_live_security_defaults(app: Flask) -> None:
    """Production/staging icin zorunlu guvenlik ayarlarini dogrula."""
    app_env = (app.config.get("APP_ENV") or "development").strip().lower()
    if app_env not in {"production", "staging"}:
        return

    security_errors: list[str] = []

    secret_key = (app.config.get("SECRET_KEY") or "").strip()
    if not secret_key:
        security_errors.append("SECRET_KEY tanimli degil.")

    first_login_password = (app.config.get("DEFAULT_FIRST_LOGIN_PASSWORD") or "").strip()
    if first_login_password in {"123456", "12345678", "password", "admin", "changeme", "CHANGE_ME"}:
        security_errors.append("DEFAULT_FIRST_LOGIN_PASSWORD guvensiz/sabit deger olamaz.")

    sentry_dsn = (app.config.get("SENTRY_DSN") or "").strip()
    sentry_required = bool(app.config.get("SENTRY_REQUIRED_IN_PRODUCTION", False))
    if sentry_required and not sentry_dsn:
        security_errors.append("SENTRY_DSN tanimli degil; SENTRY_REQUIRED_IN_PRODUCTION aktif.")
    if sentry_dsn and _looks_like_sentry_placeholder(sentry_dsn):
        security_errors.append("SENTRY_DSN placeholder deger olamaz.")

    if _postgres_sslmode_is_unsafe(app.config.get("SQLALCHEMY_DATABASE_URI") or ""):
        security_errors.append("PostgreSQL baglantisinda sslmode=disable canli/staging icin kullanilamaz.")

    if not app.config.get("SESSION_COOKIE_SECURE", False):
        security_errors.append("SESSION_COOKIE_SECURE production/staging icin True olmali.")

    if not app.config.get("SESSION_COOKIE_HTTPONLY", False):
        security_errors.append("SESSION_COOKIE_HTTPONLY production/staging icin True olmali.")

    session_cookie_samesite = str(app.config.get("SESSION_COOKIE_SAMESITE", "") or "").strip().lower()
    if session_cookie_samesite not in {"lax", "strict"}:
        security_errors.append("SESSION_COOKIE_SAMESITE production/staging icin Lax veya Strict olmali.")

    if not app.config.get("REMEMBER_COOKIE_SECURE", False):
        security_errors.append("REMEMBER_COOKIE_SECURE production/staging icin True olmali.")

    if int(app.config.get("WTF_CSRF_TIME_LIMIT", 0) or 0) <= 0:
        security_errors.append("WTF_CSRF_TIME_LIMIT pozitif bir deger olmali.")

    if int(app.config.get("LOGIN_CAPTCHA_THRESHOLD", 0) or 0) < 3:
        security_errors.append("LOGIN_CAPTCHA_THRESHOLD en az 3 olmali.")

    if not app.config.get("TCKN_ENCRYPTION_KEY"):
        app.logger.warning("TCKN_ENCRYPTION_KEY tanimli degil; hassas kimlik verisi modulu acik kalacaksa canliya cikmadan once anahtar set edin.")

    if bool(app.config.get("CSP_REPORT_ONLY", True)):
        app.logger.warning("CSP_REPORT_ONLY aktif. Canliya cikmadan once gerekiyorsa enforce moduna alin.")

    redis_warning = app.config.get("REDIS_CONFIG_WARNING") or app.config.get("CACHE_REDIS_CONFIG_WARNING") or app.config.get("SECURITY_RATE_LIMIT_REDIS_CONFIG_WARNING")
    if redis_warning:
        app.logger.warning("Redis ayari guvenli fallback'e alindi: %s", redis_warning)

    if app.config.get("AI_REQUIRE_REAL_PROVIDER_FOR_USER_VISIBLE"):
        try:
            from app.services.ai.client import get_provider_snapshot
            provider = get_provider_snapshot()
            if not provider.get("ready_for_live_provider"):
                security_errors.append("Kullaniciya gorunen AI icin gercek saglayici zorunlu; AI_BASE_URL/AI_API_KEY eksik.")
        except Exception as exc:
            logger.exception("BYS360 critical exception captured in app/security/startup_audit.py", exc_info=exc)
            security_errors.append(f"AI saglayici denetimi calisamadi: {exc}")

    script_src = str(app.config.get("CSP_SCRIPT_SRC", "") or "")
    if "'unsafe-inline'" in script_src and not bool(app.config.get("CSP_ALLOW_UNSAFE_INLINE_SCRIPT", False)):
        security_errors.append("CSP_SCRIPT_SRC icinde unsafe-inline bulunamaz; nonce tabanli CSP kullanilmalidir.")

    if security_errors:
        raise RuntimeError("Canli guvenlik ayarlari eksik: " + " | ".join(security_errors))


def run_startup_security_audit(app: Flask) -> None:
    """Mevcut runtime guvenlik ozetini tek giris noktasindan logla."""
    log_runtime_security_posture(app)


__all__ = ["validate_live_security_defaults", "run_startup_security_audit"]
