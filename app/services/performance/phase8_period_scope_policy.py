"""
BYS360 Performans Tamamlama Faz 8
Çoklu Dönem ve Özel Grup Dönemleri Politika Merkezi

Amaç:
- Aynı yıl içinde yıllık, 6 aylık, 3 aylık, aylık ve özel dönemleri desteklemek.
- Dönem kapsamını tüm kurum, birim, üst birim, kategori/grup veya seçili personel olarak yönetmek.
- Güvenlik/Temizlik gibi kategori özel dönemleri için görev üretimini yalnızca kapsam personeline sınırlamak.
- Aynı personel için çakışan tarih aralığı dönemlerini uyarı statüsüne almak.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)


PHASE8_POLICY_MARKER = "BYS360_PERFORMANCE_COMPLETION_PHASE8_PERIOD_SCOPE_POLICY"

PERIOD_TYPES = {
    "annual": "Yıllık",
    "semiannual": "6 Aylık",
    "quarterly": "3 Aylık",
    "monthly": "Aylık",
    "special": "Özel Dönem",
}

SCOPE_TYPES = {
    "all": "Tüm Kurum",
    "unit": "Birim",
    "parent_unit": "Üst Birim",
    "category": "Kategori/Grup",
    "selected_personnel": "Seçili Personel",
}

SPECIAL_PERIOD_REASONS = {
    "trial": "Deneme Süreli Personel",
    "leaving": "Ayrılacak Personel",
    "security": "Güvenlik Grubu Özel Dönemi",
    "cleaning": "Temizlik Grubu Özel Dönemi",
    "other": "Diğer Özel Dönem",
}


@dataclass(frozen=True)
class PeriodScopeDecision:
    valid: bool
    period_type: str
    period_type_label: str
    scope_type: str
    scope_type_label: str
    requires_scope_value: bool
    assignment_limited: bool
    label: str
    errors: tuple[str, ...]


@dataclass(frozen=True)
class PeriodOverlapDecision:
    has_overlap: bool
    severity: str
    label: str
    conflicting_period_ids: tuple[Any, ...]


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/phase8_period_scope_policy.py")
    return None


def normalize_period_type(value: Any) -> str:
    raw = str(value or "annual").strip().lower()
    aliases = {
        "yillik": "annual",
        "yıllık": "annual",
        "annual": "annual",
        "yearly": "annual",
        "6": "semiannual",
        "6 aylık": "semiannual",
        "6 aylik": "semiannual",
        "semiannual": "semiannual",
        "half": "semiannual",
        "3": "quarterly",
        "3 aylık": "quarterly",
        "3 aylik": "quarterly",
        "quarterly": "quarterly",
        "aylık": "monthly",
        "aylik": "monthly",
        "monthly": "monthly",
        "özel": "special",
        "ozel": "special",
        "special": "special",
    }
    return aliases.get(raw, "annual")


def normalize_scope_type(value: Any) -> str:
    raw = str(value or "all").strip().lower()
    aliases = {
        "all": "all",
        "tum": "all",
        "tüm": "all",
        "kurum": "all",
        "unit": "unit",
        "birim": "unit",
        "parent_unit": "parent_unit",
        "ust_birim": "parent_unit",
        "üst birim": "parent_unit",
        "category": "category",
        "kategori": "category",
        "grup": "category",
        "group": "category",
        "selected": "selected_personnel",
        "selected_personnel": "selected_personnel",
        "secilen": "selected_personnel",
        "seçili personel": "selected_personnel",
    }
    return aliases.get(raw, "all")


def resolve_period_scope(
    *,
    period_type: Any = "annual",
    scope_type: Any = "all",
    scope_value: Any = None,
    selected_personnel_ids: Sequence[Any] | None = None,
    start_date: Any = None,
    end_date: Any = None,
    special_reason: Any = None,
) -> PeriodScopeDecision:
    errors: list[str] = []

    ptype = normalize_period_type(period_type)
    stype = normalize_scope_type(scope_type)

    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if start and end and end < start:
        errors.append("Dönem bitiş tarihi başlangıç tarihinden önce olamaz.")

    requires_scope = stype in {"unit", "parent_unit", "category", "selected_personnel"}
    if stype in {"unit", "parent_unit", "category"} and not str(scope_value or "").strip():
        errors.append(f"{SCOPE_TYPES[stype]} kapsamı için kapsam değeri seçilmelidir.")

    selected_ids = [x for x in (selected_personnel_ids or []) if str(x or "").strip()]
    if stype == "selected_personnel" and not selected_ids:
        errors.append("Seçili personel dönemi için en az bir personel seçilmelidir.")

    if ptype == "special" and not str(special_reason or "").strip():
        errors.append("Özel dönem için gerekçe seçilmelidir.")

    scope_label = SCOPE_TYPES[stype]
    if stype in {"unit", "parent_unit", "category"} and scope_value:
        scope_label = f"{scope_label}: {scope_value}"
    if stype == "selected_personnel":
        scope_label = f"{scope_label}: {len(selected_ids)} kişi"

    period_label = PERIOD_TYPES[ptype]
    if ptype == "special" and special_reason:
        period_label = SPECIAL_PERIOD_REASONS.get(str(special_reason).strip().lower(), period_label)

    label = f"{period_label} / {scope_label}"

    return PeriodScopeDecision(
        valid=not errors,
        period_type=ptype,
        period_type_label=period_label,
        scope_type=stype,
        scope_type_label=scope_label,
        requires_scope_value=requires_scope,
        assignment_limited=stype != "all",
        label=label,
        errors=tuple(errors),
    )


def _period_dates(period: Mapping[str, Any]) -> tuple[date | None, date | None]:
    return (
        _parse_date(period.get("start_date") or period.get("start") or period.get("baslangic_tarihi")),
        _parse_date(period.get("end_date") or period.get("end") or period.get("bitis_tarihi")),
    )


def detect_period_overlap(
    *,
    employee_id: Any,
    new_start_date: Any,
    new_end_date: Any,
    existing_periods: Iterable[Mapping[str, Any]],
) -> PeriodOverlapDecision:
    employee_raw = str(employee_id or "").strip()
    new_start = _parse_date(new_start_date)
    new_end = _parse_date(new_end_date)
    conflicts: list[Any] = []

    if not employee_raw or not new_start or not new_end:
        return PeriodOverlapDecision(False, "none", "Çakışma kontrolü için yeterli veri yok.", tuple())

    for period in existing_periods or []:
        period_employee = str(period.get("employee_id") or period.get("personel_id") or "").strip()
        if period_employee and period_employee != employee_raw:
            continue

        start, end = _period_dates(period)
        if not start or not end:
            continue

        if new_start <= end and start <= new_end:
            conflicts.append(period.get("id") or period.get("period_id") or period.get("name") or period.get("title"))

    if conflicts:
        return PeriodOverlapDecision(
            has_overlap=True,
            severity="warning",
            label="Aynı personel için tarih aralığı çakışan dönem bulundu.",
            conflicting_period_ids=tuple(conflicts),
        )

    return PeriodOverlapDecision(
        has_overlap=False,
        severity="none",
        label="Dönem tarih aralığında çakışma bulunmadı.",
        conflicting_period_ids=tuple(),
    )


def filter_personnel_for_period_scope(
    personnel_rows: Iterable[Mapping[str, Any]],
    *,
    scope_type: Any = "all",
    scope_value: Any = None,
    selected_personnel_ids: Sequence[Any] | None = None,
) -> list[dict[str, Any]]:
    stype = normalize_scope_type(scope_type)
    selected = {str(x) for x in (selected_personnel_ids or []) if str(x or "").strip()}
    scope_raw = str(scope_value or "").strip().lower()

    filtered: list[dict[str, Any]] = []
    for row in personnel_rows or []:
        item = dict(row)
        if stype == "all":
            filtered.append(item)
            continue

        if stype == "selected_personnel":
            rid = str(item.get("id") or item.get("employee_id") or item.get("personel_id") or "")
            if rid in selected:
                filtered.append(item)
            continue

        if stype == "category":
            category = str(item.get("personnel_category") or item.get("category") or item.get("kategori") or "").strip().lower()
            if category == scope_raw:
                filtered.append(item)
            continue

        if stype == "unit":
            unit = str(item.get("unit") or item.get("birim") or item.get("unit_id") or "").strip().lower()
            if unit == scope_raw:
                filtered.append(item)
            continue

        if stype == "parent_unit":
            parent = str(item.get("parent_unit") or item.get("ust_birim") or item.get("üst_birim") or item.get("parent_unit_id") or "").strip().lower()
            if parent == scope_raw:
                filtered.append(item)
            continue

    return filtered


def build_assignment_scope_payload(
    personnel_rows: Iterable[Mapping[str, Any]],
    *,
    period_type: Any,
    scope_type: Any,
    scope_value: Any = None,
    selected_personnel_ids: Sequence[Any] | None = None,
    start_date: Any = None,
    end_date: Any = None,
    special_reason: Any = None,
) -> dict[str, Any]:
    decision = resolve_period_scope(
        period_type=period_type,
        scope_type=scope_type,
        scope_value=scope_value,
        selected_personnel_ids=selected_personnel_ids,
        start_date=start_date,
        end_date=end_date,
        special_reason=special_reason,
    )
    filtered = filter_personnel_for_period_scope(
        personnel_rows,
        scope_type=decision.scope_type,
        scope_value=scope_value,
        selected_personnel_ids=selected_personnel_ids,
    )

    return {
        "valid": decision.valid,
        "period_type": decision.period_type,
        "period_type_label": decision.period_type_label,
        "scope_type": decision.scope_type,
        "scope_type_label": decision.scope_type_label,
        "assignment_limited": decision.assignment_limited,
        "assignment_count": len(filtered),
        "personnel_ids": [row.get("id") or row.get("employee_id") or row.get("personel_id") for row in filtered],
        "errors": list(decision.errors),
        "label": decision.label,
    }


def phase8_period_scope_contract() -> dict[str, Any]:
    return {
        "multiple_periods_same_year": True,
        "period_types": sorted(PERIOD_TYPES.keys()),
        "scope_types": sorted(SCOPE_TYPES.keys()),
        "category_specific_period": True,
        "selected_personnel_period": True,
        "trial_period_supported": True,
        "leaving_personnel_period_supported": True,
        "assignment_generation_scope_limited": True,
        "period_overlap_warning": True,
        "phase_marker": PHASE8_POLICY_MARKER,
    }

# BYS360_PERFORMANCE_COMPLETION_PHASE8_PERIOD_SCOPE_BOUND
# Çoklu dönem ve kapsamlı görev üretimi phase8_period_scope_policy sözleşmesini kullanır.
