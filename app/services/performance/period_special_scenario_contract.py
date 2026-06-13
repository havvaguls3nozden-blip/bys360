
"""BYS360 Faz 8.3 — Performans özel dönem senaryoları sözleşmesi.

Bu sözleşme yalnızca özel dönem senaryolarını tek merkezde tutar.
Görev üretimi kapsam filtresi Faz 8.4 içinde ayrıca bağlanacaktır.
"""
from __future__ import annotations

SCENARIO_NONE = ""
SCENARIO_SECURITY_PERSONNEL = "security_personnel"
SCENARIO_CLEANING_PERSONNEL = "cleaning_personnel"
SCENARIO_PROBATION_PERSONNEL = "probation_personnel"
SCENARIO_LEAVING_PERSONNEL = "leaving_personnel"
SCENARIO_UNIT_SPECIAL = "unit_special"
SCENARIO_SELECTED_PERSONNEL_SPECIAL = "selected_personnel_special"

SPECIAL_PERIOD_SCENARIO_OPTIONS: tuple[tuple[str, str], ...] = (
    (SCENARIO_NONE, "Senaryo seçmeyin"),
    (SCENARIO_SECURITY_PERSONNEL, "Güvenlik personeli özel dönemi"),
    (SCENARIO_CLEANING_PERSONNEL, "Temizlik personeli özel dönemi"),
    (SCENARIO_PROBATION_PERSONNEL, "Deneme süreli personel dönemi"),
    (SCENARIO_LEAVING_PERSONNEL, "Ayrılacak personel değerlendirmesi"),
    (SCENARIO_UNIT_SPECIAL, "Birime özel dönem"),
    (SCENARIO_SELECTED_PERSONNEL_SPECIAL, "Seçili personele özel dönem"),
)

ALLOWED_SPECIAL_PERIOD_SCENARIOS: tuple[str, ...] = tuple(value for value, _label in SPECIAL_PERIOD_SCENARIO_OPTIONS)

SPECIAL_PERIOD_SCENARIO_ALIASES: dict[str, str] = {
    "": SCENARIO_NONE,
    "none": SCENARIO_NONE,
    "yok": SCENARIO_NONE,
    "senaryo yok": SCENARIO_NONE,
    "security": SCENARIO_SECURITY_PERSONNEL,
    "security_personnel": SCENARIO_SECURITY_PERSONNEL,
    "guvenlik": SCENARIO_SECURITY_PERSONNEL,
    "güvenlik": SCENARIO_SECURITY_PERSONNEL,
    "güvenlik personeli": SCENARIO_SECURITY_PERSONNEL,
    "cleaning": SCENARIO_CLEANING_PERSONNEL,
    "cleaning_personnel": SCENARIO_CLEANING_PERSONNEL,
    "temizlik": SCENARIO_CLEANING_PERSONNEL,
    "temizlik personeli": SCENARIO_CLEANING_PERSONNEL,
    "probation": SCENARIO_PROBATION_PERSONNEL,
    "probation_personnel": SCENARIO_PROBATION_PERSONNEL,
    "deneme": SCENARIO_PROBATION_PERSONNEL,
    "deneme süreli": SCENARIO_PROBATION_PERSONNEL,
    "deneme sureli": SCENARIO_PROBATION_PERSONNEL,
    "deneme süreli personel": SCENARIO_PROBATION_PERSONNEL,
    "leaving": SCENARIO_LEAVING_PERSONNEL,
    "leaving_personnel": SCENARIO_LEAVING_PERSONNEL,
    "ayrilacak": SCENARIO_LEAVING_PERSONNEL,
    "ayrılacak": SCENARIO_LEAVING_PERSONNEL,
    "ayrılacak personel": SCENARIO_LEAVING_PERSONNEL,
    "unit": SCENARIO_UNIT_SPECIAL,
    "unit_special": SCENARIO_UNIT_SPECIAL,
    "birim": SCENARIO_UNIT_SPECIAL,
    "birime özel": SCENARIO_UNIT_SPECIAL,
    "birime ozel": SCENARIO_UNIT_SPECIAL,
    "selected": SCENARIO_SELECTED_PERSONNEL_SPECIAL,
    "selected_personnel_special": SCENARIO_SELECTED_PERSONNEL_SPECIAL,
    "selected_personnel": SCENARIO_SELECTED_PERSONNEL_SPECIAL,
    "seçili personel": SCENARIO_SELECTED_PERSONNEL_SPECIAL,
    "secilmis personel": SCENARIO_SELECTED_PERSONNEL_SPECIAL,
    "seçilmiş personel": SCENARIO_SELECTED_PERSONNEL_SPECIAL,
}

SPECIAL_PERIOD_SCENARIO_DEFAULTS: dict[str, dict[str, str]] = {
    SCENARIO_SECURITY_PERSONNEL: {
        "period_type": "Özel Dönem",
        "scope_type": "category",
        "scope_category_label": "Güvenlik",
    },
    SCENARIO_CLEANING_PERSONNEL: {
        "period_type": "Özel Dönem",
        "scope_type": "category",
        "scope_category_label": "Temizlik",
    },
    SCENARIO_PROBATION_PERSONNEL: {
        "period_type": "Özel Dönem",
        "scope_type": "category",
        "scope_category_label": "Deneme Süreli Personel",
    },
    SCENARIO_LEAVING_PERSONNEL: {
        "period_type": "Özel Dönem",
        "scope_type": "category",
        "scope_category_label": "Ayrılacak Personel",
    },
    SCENARIO_UNIT_SPECIAL: {
        "period_type": "Özel Dönem",
        "scope_type": "unit",
    },
    SCENARIO_SELECTED_PERSONNEL_SPECIAL: {
        "period_type": "Özel Dönem",
        "scope_type": "selected_personnel",
    },
}


def normalize_special_period_scenario(value: object) -> str:
    """Normalize form/database scenario input to a Faz 8.3 scenario code."""
    raw = str(value or "").strip()
    if raw in ALLOWED_SPECIAL_PERIOD_SCENARIOS:
        return raw
    collapsed = " ".join(raw.replace("-", "_").split())
    lowered = collapsed.lower()
    return SPECIAL_PERIOD_SCENARIO_ALIASES.get(collapsed, SPECIAL_PERIOD_SCENARIO_ALIASES.get(lowered, SCENARIO_NONE))


def get_special_period_scenario_label(value: object) -> str:
    scenario = normalize_special_period_scenario(value)
    return dict(SPECIAL_PERIOD_SCENARIO_OPTIONS).get(scenario, "Senaryo seçmeyin")


def build_special_scenario_defaults(value: object) -> dict[str, str]:
    scenario = normalize_special_period_scenario(value)
    return dict(SPECIAL_PERIOD_SCENARIO_DEFAULTS.get(scenario, {}))


def is_special_period_scenario(value: object) -> bool:
    return normalize_special_period_scenario(value) != SCENARIO_NONE


def scenario_uses_category_scope(value: object) -> bool:
    return build_special_scenario_defaults(value).get("scope_type") == "category"


def scenario_uses_unit_scope(value: object) -> bool:
    return build_special_scenario_defaults(value).get("scope_type") == "unit"


def scenario_uses_selected_personnel_scope(value: object) -> bool:
    return build_special_scenario_defaults(value).get("scope_type") == "selected_personnel"


__all__ = [
    "SCENARIO_NONE",
    "SCENARIO_SECURITY_PERSONNEL",
    "SCENARIO_CLEANING_PERSONNEL",
    "SCENARIO_PROBATION_PERSONNEL",
    "SCENARIO_LEAVING_PERSONNEL",
    "SCENARIO_UNIT_SPECIAL",
    "SCENARIO_SELECTED_PERSONNEL_SPECIAL",
    "SPECIAL_PERIOD_SCENARIO_OPTIONS",
    "ALLOWED_SPECIAL_PERIOD_SCENARIOS",
    "SPECIAL_PERIOD_SCENARIO_ALIASES",
    "SPECIAL_PERIOD_SCENARIO_DEFAULTS",
    "normalize_special_period_scenario",
    "get_special_period_scenario_label",
    "build_special_scenario_defaults",
    "is_special_period_scenario",
    "scenario_uses_category_scope",
    "scenario_uses_unit_scope",
    "scenario_uses_selected_personnel_scope",
]
