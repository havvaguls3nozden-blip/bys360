
"""Performans modülü için kod-tabanlı neden çözümleyici.

Amaç:
- route ve servislerin metin eşleştirmesine bağımlılığını azaltmak
- mevcut veritabanı şemasını bozmadan reason/reason_code mantığını ortaklaştırmak
- dict / nesne / ham string biçimindeki eski kayıtlarla geriye uyumlu kalmak
"""
from __future__ import annotations

from typing import Any

TR_CHAR_MAP = str.maketrans({
    "ç": "c", "Ç": "c",
    "ğ": "g", "Ğ": "g",
    "ı": "i", "I": "i", "İ": "i",
    "ö": "o", "Ö": "o",
    "ş": "s", "Ş": "s",
    "ü": "u", "Ü": "u",
})

INFO_REASON_CODES = {
    "president_excluded",
    "manager_chain_repaired",
    "single_manager_rule",
    "hukuk_single",
    "level3_comment_only",
    "delegated_assignment",
    "coordinator_chain_corrected",
    "group_staff_chain_corrected",
    "special_manager_corrected",
    "manager_chain_filled",
    "special_case",
}

_WARNING_FALLBACK_BY_LEVEL = {
    1: "manager_1_required",
    2: "manager_2_required",
    3: "manager_3_invalid",
}


_TEXT_PATTERNS = (
    ("baskan performans degerlendirme zincirine dahil edilmez", "president_excluded"),
    ("amir zinciri kurala gore onarildi", "manager_chain_repaired"),
    ("eksik amir zinciri kurala gore dolduruldu", "manager_chain_filled"),
    ("ozel tek amir kurali uygulandi", "single_manager_rule"),
    ("hukuk personeli tek amir kurali uygulandi", "hukuk_single"),
    ("hukuk musavirligi tek amir kurali uygulandi", "hukuk_single"),
    ("hukuk musavirligi ast-ust tek amir kurali uygulandi", "hukuk_single"),
    ("3. amir yorumcu modunda", "level3_comment_only"),
    ("3 amir yorumcu modunda", "level3_comment_only"),
    ("vekalet nedeniyle gorev ayni seviyede vekile yonlendirildi", "delegated_assignment"),
    ("koordinator zinciri guncel kurala gore", "coordinator_chain_corrected"),
    ("koordinator zinciri anayasa matrisine gore", "coordinator_chain_corrected"),
    ("koordinator zinciri faz 4 nihai matrise gore", "coordinator_chain_corrected"),
    ("calisma grubu personeli zinciri anayasa matrisine gore", "group_staff_chain_corrected"),
    ("calisma grubu personeli zinciri faz 4 nihai matrise gore", "group_staff_chain_corrected"),
    ("hukuk musaviri icin ozel baskanlik istisnasi uygulandi", "special_case"),
    ("hukuk musaviri icin 1. amir baskan, 2. amir baskan yardimcisi ozel kurali uygulandi", "special_case"),
    ("ozel kural geregi 1. amir baskan olarak duzeltildi", "special_manager_corrected"),
    ("ozel kural geregi zincir kurumsal siraya gore duzeltildi", "special_manager_corrected"),
    ("1. amir eksik veya pasif", "manager_1_required"),
    ("2. amir eksik veya pasif", "manager_2_required"),
    ("3. amir tanimli ancak gecersiz/pasif", "manager_3_invalid"),
    ("ayni kisi birden fazla amir seviyesine atanmis", "duplicate_manager"),
    ("personel kendisine amir atanamaz", "self_manager"),
    ("baskan kaydi bulunamadi veya pasif", "president_missing"),
)


_EVENT_TYPE_CODE_MAP = {
    "special_case": "special_case",
}


KNOWN_REASON_CODES = INFO_REASON_CODES | {
    "info_note",
    "manager_1_required",
    "manager_2_required",
    "manager_3_invalid",
    "duplicate_manager",
    "self_manager",
    "president_missing",
}


def _safe_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def normalize_reason_text(value: Any) -> str:
    text = _safe_str(value)
    if not text:
        return ""
    return " ".join(text.translate(TR_CHAR_MAP).lower().split())


def reason_message(item: Any, default: str = "") -> str:
    if item is None:
        return default
    if isinstance(item, dict):
        for key in ("message", "reason", "label", "text"):
            value = _safe_str(item.get(key))
            if value:
                return value
        return default
    for attr in ("message", "reason", "label", "text"):
        value = _safe_str(getattr(item, attr, ""))
        if value:
            return value
    return _safe_str(item) or default


def reason_code(
    item: Any = None,
    *,
    event_type: str | None = None,
    manager_level: int | None = None,
) -> str:
    if isinstance(item, dict):
        explicit = _safe_str(item.get("code") or item.get("reason_code"))
        if explicit:
            return explicit
    else:
        explicit = _safe_str(getattr(item, "code", "") or getattr(item, "reason_code", ""))
        if explicit:
            return explicit

    message = reason_message(item)
    normalized = normalize_reason_text(message)
    if normalized in KNOWN_REASON_CODES:
        return normalized

    event_key = normalize_reason_text(event_type)
    if event_key in _EVENT_TYPE_CODE_MAP:
        return _EVENT_TYPE_CODE_MAP[event_key]

    for pattern, code in _TEXT_PATTERNS:
        if pattern in normalized:
            return code

    try:
        level = int(manager_level) if manager_level is not None and _safe_str(manager_level) else None
    except (TypeError, ValueError):
        level = None

    if level in _WARNING_FALLBACK_BY_LEVEL and (
        "bulunamadi" in normalized or "eksik" in normalized or "gecersiz" in normalized or "pasif" in normalized
    ):
        return _WARNING_FALLBACK_BY_LEVEL[level]

    return ""


def reason_payload(
    item: Any = None,
    *,
    event_type: str | None = None,
    manager_level: int | None = None,
) -> dict[str, Any]:
    if isinstance(item, dict):
        level = _safe_str(item.get("level") or item.get("severity"))
    else:
        level = _safe_str(getattr(item, "level", "") or getattr(item, "severity", ""))

    return {
        "code": reason_code(item, event_type=event_type, manager_level=manager_level),
        "message": reason_message(item),
        "level": level,
    }


def is_informational_reason(
    item: Any = None,
    *,
    event_type: str | None = None,
    manager_level: int | None = None,
) -> bool:
    code = reason_code(item, event_type=event_type, manager_level=manager_level)
    if code in INFO_REASON_CODES:
        return True

    payload = reason_payload(item, event_type=event_type, manager_level=manager_level)
    if payload.get("level", "").lower() == "info":
        return True

    return False


__all__ = [
    "INFO_REASON_CODES",
    "KNOWN_REASON_CODES",
    "is_informational_reason",
    "normalize_reason_text",
    "reason_code",
    "reason_message",
    "reason_payload",
]