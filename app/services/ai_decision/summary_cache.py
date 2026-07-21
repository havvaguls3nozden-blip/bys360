from __future__ import annotations

from app.core.datetime_utils import utc_now

"""AI özet cache ve güvenli özetleme servis köprüsü.

Faz 2 canlı davranış değiştirmez. Bu dosya ``AISummaryCache`` tablo
sözleşmesine uygun cache anahtarı, kaynak hash, TTL ve güvenli özet payload
yardımcıları sunar. DB sorgusu, veritabanı commit işlemi veya dış AI çağrısı
yapmaz; route/servis katmanı isterse buradaki payloadları kullanır.

Tasarım ilkeleri:
- redact_before_prompt: özetlenecek metin önce maskelemeden geçer.
- log_minimization: cache payloadında ham veri değil özet ve hash tutulur.
- deterministic_cache_key: aynı kaynak aynı cache anahtarını üretir.
- human_review: çıktı karar değil, karar destek notudur.
"""

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

from .live_scope import LIVE_AI_DOMAIN_KEYS, LIVE_AI_TABLE_NAMES
from .logging_bridge import (
    normalize_ai_feature_type,
    normalize_ai_module_type,
    truncate_ai_log_text,
)
from .redaction_bridge import (
    apply_ai_redaction_rules,
    build_ai_redaction_context,
    redact_text_for_ai_log,
)

DEFAULT_SUMMARY_KIND = "safe_summary"
DEFAULT_PROMPT_VERSION = "faz2_safe_summary_v1"
DEFAULT_SUMMARY_TTL_SECONDS = 3600
DEFAULT_SUMMARY_LIMIT = 1200
DEFAULT_SOURCE_LIMIT = 8000
DEFAULT_CACHE_KEY_LIMIT = 255
SUMMARY_VISIBILITY_SCOPES = frozenset({"admin", "manager", "hr", "unit_manager", "self", "internal"})


@dataclass(frozen=True)
class AISummaryCachePayload:
    module_type: str
    target_table: str | None = None
    target_id: int | None = None
    summary_kind: str = DEFAULT_SUMMARY_KIND
    summary_text: str = ""
    source_hash: str = ""
    expires_at: str | None = None
    cache_key: str | None = None
    prompt_version: str = DEFAULT_PROMPT_VERSION
    was_masked: bool = True
    source_count: int = 0
    visibility_scope: str = "internal"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AISummaryCacheHit:
    hit: bool
    expired: bool
    cache_key: str | None = None
    summary_text: str | None = None
    reason: str = "miss"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _get_attr(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, Mapping):
        return row.get(key, default)
    return getattr(row, key, default)


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime,)):
        return value.isoformat(timespec="seconds")
    return str(value)


def normalize_summary_kind(value: Any) -> str:
    return normalize_ai_feature_type(value or DEFAULT_SUMMARY_KIND)[:80] or DEFAULT_SUMMARY_KIND


def normalize_visibility_scope(value: Any) -> str:
    scope = normalize_ai_module_type(value or "internal")
    return scope if scope in SUMMARY_VISIBILITY_SCOPES else "internal"


def stable_json_dumps(value: Any) -> str:
    """Hash için sıralı ve deterministik JSON metni üretir."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=_json_default, separators=(",", ":"))


def build_ai_source_hash(source_data: Any) -> str:
    text = stable_json_dumps(source_data)
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def build_ai_summary_cache_key(
    *,
    module_type: str,
    target_table: str | None = None,
    target_id: int | None = None,
    summary_kind: str = DEFAULT_SUMMARY_KIND,
    source_hash: str,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
) -> str:
    raw = "|".join(
        [
            normalize_ai_module_type(module_type),
            _clean(target_table, "general")[:100],
            str(_int_or_none(target_id) or 0),
            normalize_summary_kind(summary_kind),
            _clean(prompt_version, DEFAULT_PROMPT_VERSION),
            _clean(source_hash)[:64],
        ]
    )
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:DEFAULT_CACHE_KEY_LIMIT]


def build_ai_summary_expires_at(ttl_seconds: int | None = None, *, now: datetime | None = None) -> str:
    base = now or utc_now()
    ttl = int(ttl_seconds or DEFAULT_SUMMARY_TTL_SECONDS)
    if ttl < 60:
        ttl = 60
    return (base + timedelta(seconds=ttl)).isoformat(timespec="seconds")


def _coerce_source_items(source_data: Any) -> list[Any]:
    if source_data is None:
        return []
    if isinstance(source_data, list):
        return source_data
    if isinstance(source_data, tuple):
        return list(source_data)
    return [source_data]


def flatten_ai_summary_source_text(source_data: Any, *, limit: int = DEFAULT_SOURCE_LIMIT) -> str:
    """Ham veri kalıcılaştırmadan özet için kısa kaynak metni üretir."""
    items = _coerce_source_items(source_data)
    parts: list[str] = []
    for item in items:
        if isinstance(item, Mapping):
            safe_pairs = []
            for key, value in item.items():
                if value in (None, ""):
                    continue
                safe_pairs.append(f"{key}: {value}")
            parts.append("; ".join(safe_pairs))
        else:
            parts.append(str(item))
    return truncate_ai_log_text("\n".join(part for part in parts if part).strip(), limit=limit) or ""


def summarize_text_safely(text: Any, *, max_chars: int = DEFAULT_SUMMARY_LIMIT) -> str:
    """Dış model çağırmadan deterministik, kısa ve güvenli özet üretir.

    Bu fonksiyon geçici bir fallback özetleyicidir. Nihai AI sağlayıcısı sonraki
    fazlarda bağlansa bile cache/prompt öncesi güvenli özet sözleşmesi burada kalır.
    """
    cleaned = re.sub(r"\s+", " ", _clean(text)).strip()
    if not cleaned:
        return "Özetlenecek güvenli içerik bulunamadı."
    if len(cleaned) <= max_chars:
        return cleaned
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    summary_parts: list[str] = []
    total = 0
    for sentence in sentences:
        if not sentence:
            continue
        next_len = total + len(sentence) + 1
        if next_len > max_chars:
            break
        summary_parts.append(sentence)
        total = next_len
    summary = " ".join(summary_parts).strip() or cleaned[: max_chars - 1].rstrip()
    return summary.rstrip() + "…"


def build_ai_safe_summary_text(
    source_data: Any,
    *,
    redaction_rules: Iterable[Any] | None = None,
    module_type: str = "general",
    max_chars: int = DEFAULT_SUMMARY_LIMIT,
) -> dict[str, Any]:
    source_text = flatten_ai_summary_source_text(source_data)
    redaction_context = build_ai_redaction_context(redaction_rules or [], module_type=module_type)
    redacted_payload = apply_ai_redaction_rules(
        {"content": source_text},
        redaction_context.get("rules", []),
    )
    redacted_text = str(redacted_payload.get("content", source_text))
    safe_text = redact_text_for_ai_log(redacted_text)
    return {
        "summary_text": summarize_text_safely(safe_text, max_chars=max_chars),
        "was_masked": safe_text != source_text,
        "source_length": len(source_text),
        "safe_length": len(safe_text),
        "rule_count": int(redaction_context.get("rule_count", 0) or 0),
    }


def build_ai_summary_cache_payload(
    *,
    module_type: str,
    source_data: Any,
    target_table: str | None = None,
    target_id: int | None = None,
    summary_kind: str = DEFAULT_SUMMARY_KIND,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    ttl_seconds: int | None = None,
    redaction_rules: Iterable[Any] | None = None,
    visibility_scope: str = "internal",
    now: datetime | None = None,
) -> dict[str, Any]:
    source_items = _coerce_source_items(source_data)
    source_hash = build_ai_source_hash(source_data)
    summary = build_ai_safe_summary_text(
        source_data,
        redaction_rules=redaction_rules,
        module_type=module_type,
    )
    cache_key = build_ai_summary_cache_key(
        module_type=module_type,
        target_table=target_table,
        target_id=target_id,
        summary_kind=summary_kind,
        source_hash=source_hash,
        prompt_version=prompt_version,
    )
    return AISummaryCachePayload(
        module_type=normalize_ai_module_type(module_type),
        target_table=_clean(target_table)[:100] or None,
        target_id=_int_or_none(target_id),
        summary_kind=normalize_summary_kind(summary_kind),
        summary_text=summary["summary_text"],
        source_hash=source_hash,
        expires_at=build_ai_summary_expires_at(ttl_seconds, now=now),
        cache_key=cache_key,
        prompt_version=_clean(prompt_version, DEFAULT_PROMPT_VERSION)[:50],
        was_masked=bool(summary["was_masked"]),
        source_count=len(source_items),
        visibility_scope=normalize_visibility_scope(visibility_scope),
    ).to_dict()


def build_ai_summary_cache_record(model_cls: Any, **kwargs: Any) -> Any:
    """AISummaryCache modeli verilirse instance döndürür; commit yapmaz."""
    payload = build_ai_summary_cache_payload(**kwargs)
    allowed_fields = {
        "module_type",
        "target_table",
        "target_id",
        "summary_kind",
        "summary_text",
        "source_hash",
        "expires_at",
    }
    model_payload = {key: payload[key] for key in allowed_fields if key in payload}
    return model_cls(**model_payload)


def parse_ai_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00").replace("+00:00", ""))
    except ValueError:
        return None


def is_ai_summary_cache_fresh(row: Any, *, expected_source_hash: str | None = None, now: datetime | None = None) -> bool:
    expires_at = parse_ai_datetime(_get_attr(row, "expires_at"))
    if not expires_at:
        return False
    if expires_at <= (now or utc_now()):
        return False
    if expected_source_hash and _clean(_get_attr(row, "source_hash")) != expected_source_hash:
        return False
    return bool(_clean(_get_attr(row, "summary_text")))


def build_ai_summary_cache_hit(
    row: Any | None,
    *,
    expected_source_hash: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    if row is None:
        return AISummaryCacheHit(hit=False, expired=False, reason="not_found").to_dict()
    expires_at = parse_ai_datetime(_get_attr(row, "expires_at"))
    expired = bool(expires_at and expires_at <= (now or utc_now()))
    fresh = is_ai_summary_cache_fresh(row, expected_source_hash=expected_source_hash, now=now)
    return AISummaryCacheHit(
        hit=fresh,
        expired=expired,
        cache_key=_clean(_get_attr(row, "cache_key")) or None,
        summary_text=_clean(_get_attr(row, "summary_text")) or None,
        reason="hit" if fresh else ("expired" if expired else "stale_or_empty"),
    ).to_dict()


def build_ai_summary_cache_lookup(
    *,
    module_type: str,
    source_data: Any,
    target_table: str | None = None,
    target_id: int | None = None,
    summary_kind: str = DEFAULT_SUMMARY_KIND,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
) -> dict[str, Any]:
    source_hash = build_ai_source_hash(source_data)
    cache_key = build_ai_summary_cache_key(
        module_type=module_type,
        target_table=target_table,
        target_id=target_id,
        summary_kind=summary_kind,
        source_hash=source_hash,
        prompt_version=prompt_version,
    )
    return {
        "module_type": normalize_ai_module_type(module_type),
        "target_table": _clean(target_table)[:100] or None,
        "target_id": _int_or_none(target_id),
        "summary_kind": normalize_summary_kind(summary_kind),
        "source_hash": source_hash,
        "cache_key": cache_key,
        "prompt_version": _clean(prompt_version, DEFAULT_PROMPT_VERSION)[:50],
    }


def build_ai_summary_cache_contract() -> dict[str, Any]:
    return {
        "table": "ai_summary_cache",
        "model_hint": "AISummaryCache",
        "behavior_change": False,
        "database_change": False,
        "external_ai_call": False,
        "commit_policy": "commit yapmaz; çağıran servis yönetir",
        "required_columns": [
            "module_type",
            "target_table",
            "target_id",
            "summary_kind",
            "summary_text",
            "source_hash",
            "expires_at",
        ],
        "live_ai_tables": list(LIVE_AI_TABLE_NAMES),
        "live_domain_keys": list(LIVE_AI_DOMAIN_KEYS),
        "safety": ["redact_before_prompt", "source_hash", "ttl", "log_minimization", "role_visibility"],
    }
