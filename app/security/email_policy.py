from __future__ import annotations

from flask import current_app

DEFAULT_ALLOWED_EMAIL_DOMAINS = ("ktb.gov.tr",)


def get_allowed_email_domains() -> tuple[str, ...]:
    raw = current_app.config.get("ALLOWED_EMAIL_DOMAINS", DEFAULT_ALLOWED_EMAIL_DOMAINS)
    if isinstance(raw, str):
        items = [item.strip().lower() for item in raw.split(",") if item.strip()]
    else:
        items = [str(item).strip().lower() for item in (raw or DEFAULT_ALLOWED_EMAIL_DOMAINS) if str(item).strip()]
    return tuple(dict.fromkeys(items or list(DEFAULT_ALLOWED_EMAIL_DOMAINS)))


def normalize_email(value: str | None) -> str:
    return (value or "").strip().lower()


def is_allowed_corporate_email(email: str | None) -> bool:
    normalized = normalize_email(email)
    if not normalized or "@" not in normalized:
        return False
    _, domain = normalized.rsplit("@", 1)
    return domain in set(get_allowed_email_domains())


def corporate_email_error_message() -> str:
    domains = ", ".join(f"@{item}" for item in get_allowed_email_domains())
    return f"Yalnız kurumsal e-posta adresleri kabul edilir: {domains}."