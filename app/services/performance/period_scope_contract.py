
"""BYS360 Faz 8.2 — Performans dönemi kapsam sözleşmesi.

Bu sözleşme yalnızca dönem kapsam tiplerini tek merkezde tutar.
Görev üretimi kapsam filtresi Faz 8.4 içinde ayrıca bağlanacaktır.
"""
from __future__ import annotations

SCOPE_ALL = "all"
SCOPE_UNIT = "unit"
SCOPE_UPPER_UNIT = "upper_unit"
SCOPE_CATEGORY = "category"
SCOPE_SELECTED_PERSONNEL = "selected_personnel"

PERIOD_SCOPE_OPTIONS: tuple[tuple[str, str], ...] = (
    (SCOPE_ALL, "Tüm Kurum"),
    (SCOPE_UNIT, "Birim"),
    (SCOPE_UPPER_UNIT, "Üst Birim"),
    (SCOPE_CATEGORY, "Kategori"),
    (SCOPE_SELECTED_PERSONNEL, "Seçili Personel"),
)

ALLOWED_PERIOD_SCOPE_TYPES: tuple[str, ...] = tuple(value for value, _label in PERIOD_SCOPE_OPTIONS)

PERIOD_SCOPE_ALIASES: dict[str, str] = {
    "": SCOPE_ALL,
    "all": SCOPE_ALL,
    "tum_kurum": SCOPE_ALL,
    "tüm kurum": SCOPE_ALL,
    "tum kurum": SCOPE_ALL,
    "kurum": SCOPE_ALL,
    "unit": SCOPE_UNIT,
    "birim": SCOPE_UNIT,
    "belirli birim": SCOPE_UNIT,
    "belirli birim / grup": SCOPE_UNIT,
    "grup": SCOPE_UNIT,
    "upper_unit": SCOPE_UPPER_UNIT,
    "ust_birim": SCOPE_UPPER_UNIT,
    "üst_birim": SCOPE_UPPER_UNIT,
    "ust birim": SCOPE_UPPER_UNIT,
    "üst birim": SCOPE_UPPER_UNIT,
    "category": SCOPE_CATEGORY,
    "kategori": SCOPE_CATEGORY,
    "personel kategorisi": SCOPE_CATEGORY,
    "selected_personnel": SCOPE_SELECTED_PERSONNEL,
    "selected-personnel": SCOPE_SELECTED_PERSONNEL,
    "secilmis_personel": SCOPE_SELECTED_PERSONNEL,
    "seçilmiş_personel": SCOPE_SELECTED_PERSONNEL,
    "secilmis personel": SCOPE_SELECTED_PERSONNEL,
    "seçilmiş personel": SCOPE_SELECTED_PERSONNEL,
    "seçili personel": SCOPE_SELECTED_PERSONNEL,
}


def normalize_period_scope_type(value: object) -> str:
    """Normalize form/database scope input to a Faz 8.2 scope type."""
    raw = str(value or "").strip()
    if raw in ALLOWED_PERIOD_SCOPE_TYPES:
        return raw
    collapsed = " ".join(raw.replace("-", "_").split())
    if collapsed in PERIOD_SCOPE_ALIASES:
        return PERIOD_SCOPE_ALIASES[collapsed]
    lowered = collapsed.lower()
    return PERIOD_SCOPE_ALIASES.get(lowered, SCOPE_ALL)


def get_period_scope_label(value: object) -> str:
    scope_type = normalize_period_scope_type(value)
    return dict(PERIOD_SCOPE_OPTIONS).get(scope_type, "Tüm Kurum")


def is_valid_period_scope_type(value: object) -> bool:
    return normalize_period_scope_type(value) in ALLOWED_PERIOD_SCOPE_TYPES


def is_specific_period_scope(value: object) -> bool:
    return normalize_period_scope_type(value) != SCOPE_ALL


def scope_uses_unit_label(value: object) -> bool:
    return normalize_period_scope_type(value) in {SCOPE_UNIT, SCOPE_UPPER_UNIT}


def scope_uses_category_label(value: object) -> bool:
    return normalize_period_scope_type(value) == SCOPE_CATEGORY


def scope_uses_personnel_filter(value: object) -> bool:
    return normalize_period_scope_type(value) == SCOPE_SELECTED_PERSONNEL


__all__ = [
    "SCOPE_ALL",
    "SCOPE_UNIT",
    "SCOPE_UPPER_UNIT",
    "SCOPE_CATEGORY",
    "SCOPE_SELECTED_PERSONNEL",
    "PERIOD_SCOPE_OPTIONS",
    "ALLOWED_PERIOD_SCOPE_TYPES",
    "PERIOD_SCOPE_ALIASES",
    "normalize_period_scope_type",
    "get_period_scope_label",
    "is_valid_period_scope_type",
    "is_specific_period_scope",
    "scope_uses_unit_label",
    "scope_uses_category_label",
    "scope_uses_personnel_filter",
]
