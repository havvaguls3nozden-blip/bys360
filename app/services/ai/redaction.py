from __future__ import annotations



import re
from typing import Any


EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
LONG_NUMBER_RE = re.compile(r"\b\d{8,11}\b")

REDACT_KEYS = {
    "email",
    "e_posta",
    "email_address",
    "manual_email",
    "tckn",
    "tc_kimlik_no",
    "identity_no",
    "phone",
    "manual_phone",
}


def _mask_email(text: str) -> str:
    return EMAIL_RE.sub(lambda m: f"***@{m.group(2)}", text)


def _mask_long_number(text: str) -> str:
    return LONG_NUMBER_RE.sub("***", text)


def redact_text(value: Any) -> str:
    text = str(value or "")
    text = _mask_email(text)
    text = _mask_long_number(text)
    return text


def redact_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        result = {}
        for key, value in payload.items():
            normalized_key = str(key).strip().lower()
            if normalized_key in REDACT_KEYS:
                result[key] = "***"
            else:
                result[key] = redact_payload(value)
        return result
    if isinstance(payload, list):
        return [redact_payload(item) for item in payload]
    if isinstance(payload, tuple):
        return tuple(redact_payload(item) for item in payload)
    if isinstance(payload, str):
        return redact_text(payload)
    return payload