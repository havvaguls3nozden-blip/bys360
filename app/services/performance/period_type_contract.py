
"""BYS360 Faz 8.1 — Performans dönemi türleri sözleşmesi.

Bu dosya dönem türlerini tek merkezde tutar. Faz 8.1 yalnızca dönem türü
sözleşmesini güçlendirir; dönem kapsamı ve görev üretimi Faz 8.2+ içinde
ele alınacaktır.
"""
from __future__ import annotations

PERIOD_TYPE_MONTHLY = "Aylık"
PERIOD_TYPE_QUARTERLY = "3 Aylık"
PERIOD_TYPE_SEMI_ANNUAL = "6 Aylık"
PERIOD_TYPE_ANNUAL = "Yıllık"
PERIOD_TYPE_SPECIAL = "Özel Dönem"

PERIOD_TYPE_OPTIONS: tuple[tuple[str, str], ...] = (
    (PERIOD_TYPE_MONTHLY, "Aylık"),
    (PERIOD_TYPE_QUARTERLY, "3 Aylık"),
    (PERIOD_TYPE_SEMI_ANNUAL, "6 Aylık"),
    (PERIOD_TYPE_ANNUAL, "Yıllık"),
    (PERIOD_TYPE_SPECIAL, "Özel Dönem"),
)

ALLOWED_PERIOD_TYPES: tuple[str, ...] = tuple(value for value, _ in PERIOD_TYPE_OPTIONS)

# Eski ekranlarda "Özel" yazılmış dönemleri kırmadan yeni sözleşmeye taşır.
PERIOD_TYPE_ALIASES: dict[str, str] = {
    "": "",
    "aylik": PERIOD_TYPE_MONTHLY,
    "aylık": PERIOD_TYPE_MONTHLY,
    "Aylik": PERIOD_TYPE_MONTHLY,
    "Aylık": PERIOD_TYPE_MONTHLY,
    "3 aylik": PERIOD_TYPE_QUARTERLY,
    "3 aylık": PERIOD_TYPE_QUARTERLY,
    "3 Aylik": PERIOD_TYPE_QUARTERLY,
    "3 Aylık": PERIOD_TYPE_QUARTERLY,
    "uc aylik": PERIOD_TYPE_QUARTERLY,
    "üç aylık": PERIOD_TYPE_QUARTERLY,
    "6 aylik": PERIOD_TYPE_SEMI_ANNUAL,
    "6 aylık": PERIOD_TYPE_SEMI_ANNUAL,
    "6 Aylik": PERIOD_TYPE_SEMI_ANNUAL,
    "6 Aylık": PERIOD_TYPE_SEMI_ANNUAL,
    "alti aylik": PERIOD_TYPE_SEMI_ANNUAL,
    "altı aylık": PERIOD_TYPE_SEMI_ANNUAL,
    "yillik": PERIOD_TYPE_ANNUAL,
    "yıllık": PERIOD_TYPE_ANNUAL,
    "Yillik": PERIOD_TYPE_ANNUAL,
    "Yıllık": PERIOD_TYPE_ANNUAL,
    "ozel": PERIOD_TYPE_SPECIAL,
    "özel": PERIOD_TYPE_SPECIAL,
    "Ozel": PERIOD_TYPE_SPECIAL,
    "Özel": PERIOD_TYPE_SPECIAL,
    "ozel donem": PERIOD_TYPE_SPECIAL,
    "özel dönem": PERIOD_TYPE_SPECIAL,
    "Ozel Donem": PERIOD_TYPE_SPECIAL,
    "Özel Dönem": PERIOD_TYPE_SPECIAL,
}


def normalize_period_type(value: object) -> str:
    """Normalize user/form input to one of the Faz 8.1 period type labels."""
    raw = str(value or "").strip()
    if raw in ALLOWED_PERIOD_TYPES:
        return raw
    collapsed = " ".join(raw.split())
    if collapsed in PERIOD_TYPE_ALIASES:
        return PERIOD_TYPE_ALIASES[collapsed]
    lowered = collapsed.lower()
    return PERIOD_TYPE_ALIASES.get(lowered, collapsed)


def get_period_type_label(value: object) -> str:
    normalized = normalize_period_type(value)
    return normalized if normalized in ALLOWED_PERIOD_TYPES else str(value or "").strip()


def is_valid_period_type(value: object) -> bool:
    return normalize_period_type(value) in ALLOWED_PERIOD_TYPES


__all__ = [
    "PERIOD_TYPE_MONTHLY",
    "PERIOD_TYPE_QUARTERLY",
    "PERIOD_TYPE_SEMI_ANNUAL",
    "PERIOD_TYPE_ANNUAL",
    "PERIOD_TYPE_SPECIAL",
    "PERIOD_TYPE_OPTIONS",
    "ALLOWED_PERIOD_TYPES",
    "PERIOD_TYPE_ALIASES",
    "normalize_period_type",
    "get_period_type_label",
    "is_valid_period_type",
]
