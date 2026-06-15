from __future__ import annotations

from flask import Flask


_OBSERVABILITY_REQUIRED_ENVS = {"production", "staging", "live", "canli", "pilot"}

_PLACEHOLDER_DSN_MARKERS = (
    "https://...@sentry.io/",
    "sentry.io/...",
    "your-public-key",
    "project-id",
    "change-me",
    "CHANGE_ME",
)


def _looks_like_placeholder_dsn(dsn: str) -> bool:
    value = (dsn or "").strip()
    if not value:
        return False
    lowered = value.lower()
    return any(marker.lower() in lowered for marker in _PLACEHOLDER_DSN_MARKERS)


def configure_optional_sentry(app: Flask) -> None:
    """Sentry hata izlemeyi gercek DSN varsa etkinlestirir.

    Placeholder DSN degeri izleme varmis gibi davranmasin diye ozellikle
    reddedilir. Production/staging/live/canli/pilot ortaminda SENTRY_REQUIRED_IN_PRODUCTION=true
    ise DSN eksikligi uygulama acilisinda hata uretir; aksi halde sistem
    calismaya devam eder ve loga net uyari yazar.
    """
    dsn = (app.config.get("SENTRY_DSN") or "").strip()
    app_env = (app.config.get("APP_ENV") or "development").strip().lower()
    required = bool(app.config.get("SENTRY_REQUIRED_IN_PRODUCTION", False)) and app_env in _OBSERVABILITY_REQUIRED_ENVS

    if not dsn:
        message = "Sentry DSN tanimli degil; hata izleme kapali."
        if required:
            raise RuntimeError(message)
        app.logger.warning(message)
        app.extensions["bys360_sentry_enabled"] = False
        return

    if _looks_like_placeholder_dsn(dsn):
        message = "Sentry DSN placeholder gorunuyor; hata izleme etkinlestirilmedi."
        if required:
            raise RuntimeError(message)
        app.logger.warning(message)
        app.extensions["bys360_sentry_enabled"] = False
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    except Exception as exc:  # pragma: no cover
        message = f"Sentry kutuphanesi yuklenemedi: {exc}"
        if required:
            raise RuntimeError(message) from exc
        app.logger.warning(message)
        app.extensions["bys360_sentry_enabled"] = False
        return

    init_kwargs = {
        "dsn": dsn,
        "integrations": [
            FlaskIntegration(),
            LoggingIntegration(event_level=None),
            SqlalchemyIntegration(),
        ],
        "environment": (app.config.get("SENTRY_ENVIRONMENT") or app_env or "production"),
        "traces_sample_rate": float(app.config.get("SENTRY_TRACES_SAMPLE_RATE") or 0.0),
        "profiles_sample_rate": float(app.config.get("SENTRY_PROFILES_SAMPLE_RATE") or 0.0),
        "send_default_pii": bool(app.config.get("SENTRY_SEND_DEFAULT_PII", False)),
    }
    release = (app.config.get("SENTRY_RELEASE") or "").strip()
    if release:
        init_kwargs["release"] = release

    sentry_sdk.init(**init_kwargs)
    app.extensions["bys360_sentry_enabled"] = True
    app.logger.info("Sentry hata izleme etkinlestirildi.")
