from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, timedelta
from typing import Any, Callable

from .common import _safe_float, _safe_int
from .period_scope_contract import ALLOWED_PERIOD_SCOPE_TYPES, normalize_period_scope_type
from .period_special_scenario_contract import build_special_scenario_defaults, normalize_special_period_scenario
from .period_type_contract import ALLOWED_PERIOD_TYPES, normalize_period_type

BYS360_SCORING_AFTER_PERIOD_END_FORM_MARKER = "BYS360_PERFORMANCE_SCORING_AFTER_PERIOD_END_FORM_V1_2"


def _bool_from_form(form_data: Mapping[str, Any], field_name: str, default: bool = False) -> bool:
    value = form_data.get(field_name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "on", "yes", "evet"}


def _as_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise ValueError("Geçerli bir tarih giriniz.")


def _next_day(value: Any) -> date:
    return _as_date(value) + timedelta(days=1)


def parse_period_form(form_data: Mapping[str, Any], *, parse_date: Callable[[str], Any]) -> dict[str, Any]:
    title = str(form_data.get("title") or "").strip()
    period_type = normalize_period_type(form_data.get("period_type"))
    start_date_raw = str(form_data.get("start_date") or "").strip()
    end_date_raw = str(form_data.get("end_date") or "").strip()
    evaluation_start_date_raw = str(form_data.get("evaluation_start_date") or "").strip()
    evaluation_end_date_raw = str(form_data.get("evaluation_end_date") or "").strip()
    description = str(form_data.get("description") or "").strip()

    if not title or not period_type or not start_date_raw or not end_date_raw:
        raise ValueError("Başlık, dönem türü, başlangıç ve bitiş tarihi zorunludur.")

    # BYS360_PHASE8_1_PERIOD_TYPE_VALIDATION
    if period_type not in ALLOWED_PERIOD_TYPES:
        allowed = ", ".join(ALLOWED_PERIOD_TYPES)
        raise ValueError(f"Geçerli bir dönem türü seçiniz: {allowed}.")

    start_date = _as_date(parse_date(start_date_raw))
    end_date = _as_date(parse_date(end_date_raw))

    if start_date > end_date:
        raise ValueError("Başlangıç tarihi bitiş tarihinden büyük olamaz.")

    evaluation_due_days = _safe_int(form_data.get("evaluation_due_days"), None)
    if evaluation_due_days is not None and evaluation_due_days <= 0:
        evaluation_due_days = None

    # BYS360_PERFORMANCE_SCORING_AFTER_PERIOD_END_FORM_V1_2
    # Dönem aralığı personelin değerlendirildiği çalışma dönemidir.
    # Puanlama, dönem devam ederken açılmaz; varsayılan olarak dönem bitişinden sonraki gün başlar.
    # Eski validasyon puanlama tarihini dönem aralığının içine zorladığı için özel/genel dönem oluşturmayı engelliyordu.
    default_scoring_start = _next_day(end_date)
    evaluation_start_date = _as_date(parse_date(evaluation_start_date_raw)) if evaluation_start_date_raw else default_scoring_start
    if evaluation_start_date <= end_date:
        evaluation_start_date = default_scoring_start

    if evaluation_end_date_raw:
        evaluation_end_date = _as_date(parse_date(evaluation_end_date_raw))
        if evaluation_end_date <= end_date:
            evaluation_end_date = evaluation_start_date
    elif evaluation_due_days:
        evaluation_end_date = evaluation_start_date + timedelta(days=max(0, evaluation_due_days - 1))
    else:
        evaluation_end_date = evaluation_start_date

    if evaluation_start_date > evaluation_end_date:
        raise ValueError("Puanlama bitiş tarihi puanlama başlangıcından önce olamaz.")
    if evaluation_start_date <= end_date or evaluation_end_date <= end_date:
        raise ValueError("Puanlama takvimi dönem bittikten sonra başlamalıdır.")

    minimum_presence_days_for_evaluation = max(0.0, _safe_float(form_data.get("minimum_presence_days_for_evaluation"), 0.0) or 0.0)
    leave_skip_threshold_days = _safe_float(form_data.get("leave_skip_threshold_days"), None)
    absence_skip_threshold_days = _safe_float(form_data.get("absence_skip_threshold_days"), None)

    # BYS360_PHASE8_2_PERIOD_SCOPE_PARSE
    scope_type = normalize_period_scope_type(form_data.get("scope_type") or "all")
    if scope_type not in ALLOWED_PERIOD_SCOPE_TYPES:
        scope_type = "all"
    scope_unit_label = str(form_data.get("scope_unit_label") or form_data.get("scope_upper_unit_label") or "").strip() or None
    scope_category_label = str(form_data.get("scope_category_label") or "").strip() or None
    scope_personnel_filter = str(form_data.get("scope_personnel_filter") or "").strip() or None
    # BYS360_PHASE8_3_SPECIAL_SCENARIO_PARSE
    special_scenario_type = normalize_special_period_scenario(form_data.get("special_scenario_type") or "")
    scenario_defaults = build_special_scenario_defaults(special_scenario_type)
    if scenario_defaults:
        period_type = scenario_defaults.get("period_type") or period_type
        scope_type = scenario_defaults.get("scope_type") or scope_type
        scope_category_label = scenario_defaults.get("scope_category_label") or scope_category_label
        # Birime özel ve seçili personel senaryolarında kullanıcı ilgili alanı formdan girer.
        scope_unit_label = scope_unit_label
        scope_personnel_filter = scope_personnel_filter

    # BYS360_SPECIAL_SCOPE_REQUIRED_TARGET_VALIDATION
    # Özel kapsam boş hedefle kaydedilirse görev üretimi ya tüm kuruma yayılabilir
    # ya da hiç personele görev oluşturmayabilir. Bu nedenle yalnızca özel
    # kapsam tiplerinde hedef alanı zorunlu tutulur; Tüm Kurum genel puanlama
    # davranışı aynen korunur.
    if scope_type in {"unit", "upper_unit"} and not scope_unit_label:
        raise ValueError("Birim veya üst birim kapsamı seçildiğinde ilgili birim adı zorunludur.")
    if scope_type == "category" and not scope_category_label:
        raise ValueError("Kategori/grup kapsamı seçildiğinde personel kategorisi zorunludur.")
    if scope_type == "selected_personnel" and not scope_personnel_filter:
        raise ValueError("Seçili personel kapsamı için en az bir sicil numarası/personel seçimi zorunludur.")

    level_3_column_visible = _bool_from_form(form_data, "level_3_column_visible", _bool_from_form(form_data, "enable_level_3", False))
    scorecard_readability_mode = str(form_data.get("scorecard_readability_mode") or "kurumsal").strip() or "kurumsal"

    return {
        "title": title,
        "period_type": period_type,
        "start_date": start_date,
        "end_date": end_date,
        "evaluation_start_date": evaluation_start_date,
        "evaluation_end_date": evaluation_end_date,
        "evaluation_due_days": evaluation_due_days,
        "description": description or None,
        "scope_type": scope_type,
        "scope_unit_label": scope_unit_label,
        "scope_category_label": scope_category_label,
        "scope_personnel_filter": scope_personnel_filter,
        "special_scenario_type": special_scenario_type,
        "level_3_column_visible": level_3_column_visible,
        "scorecard_readability_mode": scorecard_readability_mode,
        "minimum_presence_days_for_evaluation": minimum_presence_days_for_evaluation,
        "leave_skip_threshold_days": leave_skip_threshold_days if leave_skip_threshold_days and leave_skip_threshold_days > 0 else None,
        "absence_skip_threshold_days": absence_skip_threshold_days if absence_skip_threshold_days and absence_skip_threshold_days > 0 else None,
        "auto_skip_if_fully_absent": _bool_from_form(form_data, "auto_skip_if_fully_absent", True),
        "manager_delegation_required": _bool_from_form(form_data, "manager_delegation_required", True),
        "enable_level_3": _bool_from_form(form_data, "enable_level_3", False),
        "enable_level_3_scoring": _bool_from_form(form_data, "enable_level_3_scoring", False),
        "require_level_3_completion_for_final": _bool_from_form(form_data, "require_level_3_completion_for_final", False),
        "scoring_auto_start_after_period": True,
    }


__all__ = ["parse_period_form", "BYS360_SCORING_AFTER_PERIOD_END_FORM_MARKER"]
