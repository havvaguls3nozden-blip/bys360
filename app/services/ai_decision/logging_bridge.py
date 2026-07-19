
"""AI request / recommendation / feedback log servis köprüsü.

Faz 1 canlı davranış değiştirmez. Bu dosya, mevcut AI route veya servisleri
isterse kullanabilsin diye güvenli payload hazırlama yardımcıları sunar. DB
modeli bu katmanda zorunlu import edilmez; böylece ``python -S`` audit ve
py_compile kontrolleri bağımsız çalışır.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from collections.abc import Mapping

from .security_contract import redact_mapping_for_ai

AI_ALLOWED_REQUEST_STATUSES = frozenset({"queued", "completed", "failed", "skipped"})
AI_ALLOWED_SEVERITIES = frozenset({"info", "low", "medium", "high", "critical"})
AI_ALLOWED_VISIBILITY_FLAGS = frozenset({"internal", "manager", "admin", "user_visible"})

DEFAULT_LOG_TEXT_LIMIT = 4000
DEFAULT_ERROR_TEXT_LIMIT = 1000
DEFAULT_TITLE_LIMIT = 255
DEFAULT_CODE_LIMIT = 50
DEFAULT_TARGET_TABLE_LIMIT = 100


@dataclass(frozen=True)
class AIRequestLogPayload:
    module_type: str
    feature_type: str
    target_table: str | None = None
    target_id: int | None = None
    user_id: int | None = None
    request_text: str | None = None
    response_text: str | None = None
    provider_name: str | None = None
    model_name: str | None = None
    prompt_version: str | None = None
    status: str = "completed"
    latency_ms: int | None = None
    token_in: int | None = None
    token_out: int | None = None
    was_masked: bool = True
    was_user_visible: bool = True
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _limit(value: Any, limit: int | None) -> str | None:
    text = _clean_text(value)
    if not text:
        return None
    if limit and len(text) > limit:
        return text[: max(0, limit - 1)].rstrip() + "…"
    return text


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def coerce_ai_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "evet", "aktif"}


def normalize_ai_code(value: Any, *, fallback: str, limit: int = DEFAULT_CODE_LIMIT) -> str:
    text = _clean_text(value).lower().replace(" ", "_").replace("-", "_")
    safe = "".join(ch for ch in text if ch.isalnum() or ch == "_").strip("_")
    return (safe or fallback)[:limit]


def normalize_ai_module_type(value: Any) -> str:
    return normalize_ai_code(value, fallback="general", limit=DEFAULT_CODE_LIMIT)


def normalize_ai_feature_type(value: Any) -> str:
    return normalize_ai_code(value, fallback="decision_support", limit=DEFAULT_CODE_LIMIT)


def normalize_ai_status(value: Any) -> str:
    status = normalize_ai_code(value, fallback="completed", limit=30)
    return status if status in AI_ALLOWED_REQUEST_STATUSES else "completed"


def normalize_ai_severity(value: Any) -> str:
    severity = normalize_ai_code(value, fallback="info", limit=20)
    return severity if severity in AI_ALLOWED_SEVERITIES else "info"


def truncate_ai_log_text(value: Any, *, limit: int = DEFAULT_LOG_TEXT_LIMIT) -> str | None:
    return _limit(value, limit)


def build_ai_request_log_payload(
    *,
    module_type: str,
    feature_type: str,
    target_table: str | None = None,
    target_id: Any = None,
    user_id: Any = None,
    request_text: Any = None,
    response_text: Any = None,
    provider_name: Any = None,
    model_name: Any = None,
    prompt_version: Any = None,
    status: Any = "completed",
    latency_ms: Any = None,
    token_in: Any = None,
    token_out: Any = None,
    was_masked: Any = True,
    was_user_visible: Any = True,
    error_message: Any = None,
    redact_payload: bool = True,
) -> dict[str, Any]:
    """AIRequestLog modeliyle uyumlu güvenli payload hazırlar."""

    request_value = request_text
    response_value = response_text
    if redact_payload:
        if isinstance(request_value, Mapping):
            request_value = redact_mapping_for_ai(dict(request_value))
        if isinstance(response_value, Mapping):
            response_value = redact_mapping_for_ai(dict(response_value))

    payload = AIRequestLogPayload(
        module_type=normalize_ai_module_type(module_type),
        feature_type=normalize_ai_feature_type(feature_type),
        target_table=_limit(target_table, DEFAULT_TARGET_TABLE_LIMIT),
        target_id=_int_or_none(target_id),
        user_id=_int_or_none(user_id),
        request_text=truncate_ai_log_text(request_value),
        response_text=truncate_ai_log_text(response_value),
        provider_name=_limit(provider_name, 100),
        model_name=_limit(model_name, 100),
        prompt_version=_limit(prompt_version, 50),
        status=normalize_ai_status(status),
        latency_ms=_int_or_none(latency_ms),
        token_in=_int_or_none(token_in),
        token_out=_int_or_none(token_out),
        was_masked=coerce_ai_bool(was_masked, default=True),
        was_user_visible=coerce_ai_bool(was_user_visible, default=True),
        error_message=_limit(error_message, DEFAULT_ERROR_TEXT_LIMIT),
    )
    return payload.to_dict()


def build_ai_request_log_update_payload(
    *,
    response_text: Any = None,
    status: Any = "completed",
    latency_ms: Any = None,
    token_in: Any = None,
    token_out: Any = None,
    error_message: Any = None,
    was_user_visible: Any | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "response_text": truncate_ai_log_text(response_text),
        "status": normalize_ai_status(status),
        "latency_ms": _int_or_none(latency_ms),
        "token_in": _int_or_none(token_in),
        "token_out": _int_or_none(token_out),
        "error_message": _limit(error_message, DEFAULT_ERROR_TEXT_LIMIT),
    }
    if was_user_visible is not None:
        payload["was_user_visible"] = coerce_ai_bool(was_user_visible, default=True)
    return payload


def build_ai_request_log_record(model_cls: type[Any], **payload_kwargs: Any) -> Any:
    """Verilen SQLAlchemy model sınıfı için kayıt nesnesi üretir; commit yapmaz."""
    payload = build_ai_request_log_payload(**payload_kwargs)
    return model_cls(**payload)


def build_ai_recommendation_payload(
    *,
    module_type: str,
    target_table: str,
    target_id: Any,
    recommendation_type: str,
    title: Any,
    body: Any = None,
    severity: Any = "info",
    status: Any = "open",
    ai_request_log_id: Any = None,
    reviewed_by_user_id: Any = None,
    reviewed_at: Any = None,
) -> dict[str, Any]:
    return {
        "module_type": normalize_ai_module_type(module_type),
        "target_table": _limit(target_table, DEFAULT_TARGET_TABLE_LIMIT) or "unknown",
        "target_id": _int_or_none(target_id) or 0,
        "recommendation_type": normalize_ai_feature_type(recommendation_type),
        "title": _limit(title, DEFAULT_TITLE_LIMIT) or "AI önerisi",
        "body": truncate_ai_log_text(body),
        "severity": normalize_ai_severity(severity),
        "status": normalize_ai_code(status, fallback="open", limit=30),
        "ai_request_log_id": _int_or_none(ai_request_log_id),
        "reviewed_by_user_id": _int_or_none(reviewed_by_user_id),
        "reviewed_at": reviewed_at if isinstance(reviewed_at, datetime) or reviewed_at is None else None,
    }


def build_ai_feedback_log_payload(
    *,
    ai_request_log_id: Any,
    user_id: Any = None,
    feedback_type: str = "useful",
    feedback_note: Any = None,
) -> dict[str, Any]:
    return {
        "ai_request_log_id": _int_or_none(ai_request_log_id) or 0,
        "user_id": _int_or_none(user_id),
        "feedback_type": normalize_ai_code(feedback_type, fallback="useful", limit=30),
        "feedback_note": _limit(feedback_note, 1000),
    }


def build_ai_safe_log_excerpt(payload: Mapping[str, Any]) -> dict[str, Any]:
    """UI veya audit için logun güvenli, kısa ve maskeleme dostu görünümü."""
    safe = dict(payload)
    for field in ("request_text", "response_text", "error_message"):
        safe[field] = _limit(safe.get(field), 240)
    safe["safe_excerpt"] = True
    return safe
