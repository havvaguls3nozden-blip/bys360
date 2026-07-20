"""Anket form verileri için saf normalizasyon yardımcıları.

Faz 3 notu:
Bu dosyadaki sabitler canlı `surveys_routes.py` davranışıyla aynı tutulur.
Fonksiyonlar veritabanına yazmaz, Flask context gerektirmez.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

SURVEY_ALLOWED_TYPES = {"kurum_ici", "memnuniyet", "egitim", "nabiz", "geri_bildirim"}
SURVEY_CREATE_ALLOWED_STATUSES = {"draft", "published", "closed"}
SURVEY_EDIT_ALLOWED_STATUSES = {"draft", "published", "closed", "archived"}
SURVEY_ALLOWED_TARGET_TYPES = {"all", "user", "role", "unit"}
SURVEY_ALLOWED_QUESTION_TYPES = {"text", "single_choice", "multiple_choice", "rating_5", "rating_10", "yes_no"}
SURVEY_ALLOWED_LOGIC_MODES = {"always", "conditional"}
SURVEY_ALLOWED_LOGIC_OPERATORS = {"answered", "selected_option", "equals", "contains", "gte", "lte"}

# Faz 2 geriye uyumluluk adları. Yeni kodlar yukarıdaki canlı adları kullanır.
SURVEY_STATUS_VALUES = SURVEY_EDIT_ALLOWED_STATUSES
SURVEY_QUESTION_TYPES = SURVEY_ALLOWED_QUESTION_TYPES
SURVEY_TARGET_TYPES = SURVEY_ALLOWED_TARGET_TYPES
SURVEY_LOGIC_MODES = SURVEY_ALLOWED_LOGIC_MODES
SURVEY_LOGIC_OPERATORS = SURVEY_ALLOWED_LOGIC_OPERATORS


def safe_text(value: Any, *, max_length: int | None = None) -> str:
    text = str(value or "").strip()
    if max_length is not None and max_length > 0:
        return text[:max_length]
    return text


def normalize_choice(value: Any, allowed_values: Iterable[str], default_value: str) -> str:
    cleaned = safe_text(value)
    allowed = {str(item) for item in (allowed_values or [])}
    return cleaned if cleaned in allowed else default_value


def dedup_preserve(items: Iterable[Any] | None) -> list[str]:
    """Canlı route davranışıyla aynı: case-insensitive tekilleştirir."""
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items or []:
        cleaned = safe_text(item)
        if not cleaned:
            continue
        lowered = cleaned.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        ordered.append(cleaned)
    return ordered


def split_option_block(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = value.replace("\\r", "").splitlines()
    elif isinstance(value, Iterable):
        raw_items = list(value)
    else:
        raw_items = [value]
    return dedup_preserve(raw_items)


def clean_target_values(
    target_type: str,
    raw_values: Iterable[Any] | None,
    *,
    roles: Iterable[str] | None = None,
    birimler: Iterable[str] | None = None,
) -> list[str]:
    """Hedef kitle değerlerini canlı route ile aynı kurala göre temizler."""
    normalized_type = normalize_choice(target_type, SURVEY_ALLOWED_TARGET_TYPES, "all")
    if normalized_type == "all":
        return []

    cleaned_values = [safe_text(value) for value in (raw_values or []) if safe_text(value)]
    if normalized_type == "user":
        deduped_ids: list[str] = []
        for value in cleaned_values:
            if not value.isdigit():
                continue
            parsed = int(value)
            if parsed <= 0:
                continue
            as_text = str(parsed)
            if as_text not in deduped_ids:
                deduped_ids.append(as_text)
        return deduped_ids

    allowed_lookup: dict[str, str] = {}
    source_values = roles if normalized_type == "role" else birimler
    for item in source_values or []:
        cleaned = safe_text(item)
        if cleaned:
            allowed_lookup.setdefault(cleaned.casefold(), cleaned)

    normalized: list[str] = []
    seen: set[str] = set()
    for value in cleaned_values:
        canonical = allowed_lookup.get(value.casefold())
        if not canonical:
            continue
        lowered = canonical.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(canonical)
    return normalized
