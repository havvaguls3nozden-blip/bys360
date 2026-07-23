from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from app.services.performance.assignments import (
    build_assignment_log_summary as _build_assignment_log_summary_mod,
)
from app.services.performance.assignments import (
    build_assignment_unit_summary as _build_assignment_unit_summary_mod,
)
from app.services.performance.assignments import (
    generate_assignments_for_active_period as _generate_assignments_for_active_period_mod,
)
from app.services.performance.assignments import (
    get_latest_assignment_generation_logs as _get_latest_assignment_generation_logs_mod,
)
from app.services.performance.assignments import (
    is_informational_special_case as _is_informational_special_case_mod,
)
from app.services.performance.common import (
    _safe_float,
    _safe_str,
    calculate_effective_weights,
    get_active_period,
    get_active_weight_config,
    get_base_weight_map,
    get_period,
    is_single_manager_case,
    normalize_weight_inputs,
)
from app.services.performance.common import (
    get_period_level_3_flags as _get_period_level_3_flags_mod,
)
from app.services.performance.criteria import (
    get_level_items_map,
    level_1_gave_any_three,
)
from app.services.performance.hierarchy import analyze_hierarchy_gaps, analyze_hierarchy_rows
from app.services.performance.orchestration import (
    build_assignment_generation_snapshot,
    build_chain_health_snapshot,
    build_performance_service_snapshot,
    build_team_compare_snapshot,
    run_assignment_generation_with_snapshot,
)
from app.services.performance.scoring import (
    calculate_preview_total_100,
    recalculate_all_evaluations,
    requires_general_comment,
    requires_level_2_comment_for_evaluation,
    save_evaluation_level,
    validate_general_comment_requirements,
    validate_score_value,
)

"""Geriye uyumlu performans servis köprüsü.

Bu dosya artık iş kuralı barındıran ana kaynak değil.
Eski route ve admin ekranları `app.services.performance_service` import etmeye
 devam ettiği için, çağrıları canlı ve güncel modüler servis katmanına yönlendirir.

Amaç:
- görev üretimini V2 / modüler çekirdeğe bağlamak
- admin kullanıcısının performans görevlerine karışmasını engellemek
- 3. amir / ağırlık / log özetlerinde tek kaynak kullanmak
- eski import yollarını bozmadan canlıyı toparlamak
"""

logger = logging.getLogger(__name__)


def _is_mapping_row(row: Any) -> bool:
    return isinstance(row, dict)


def _legacy_assignment_log_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "delegated": 0,
        "uncovered": 0,
        "exempted": 0,
        "chain_issue": 0,
        "warning": 0,
        "generated": 0,
        "cleared": 0,
        "special_case": 0,
    }
    for row in rows or []:
        event_type = _safe_str(row.get("event_type") or row.get("status")).lower()
        reason = row.get("reason")
        if _is_informational_special_case_mod(reason, event_type):
            summary["special_case"] += 1
            continue
        if event_type in summary:
            summary[event_type] += 1
            continue
        if event_type in {"tamamlandi", "completed"}:
            summary["generated"] += 1
        elif event_type in {"taslak", "draft"}:
            summary["warning"] += 1
        else:
            summary["warning"] += 1
    return summary


def _legacy_assignment_unit_summary(
    rows: list[dict[str, Any]] | None = None,
    *,
    top_n: int | None = None,
) -> list[dict[str, Any]]:
    rows = rows or []
    grouped: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "ust_birim": "",
            "birim": "",
            "total": 0,
            "completed": 0,
            "draft": 0,
            "waiting": 0,
        }
    )

    for row in rows:
        ust_birim = _safe_str(row.get("ust_birim") or row.get("employee_ust_birim"))
        birim = _safe_str(row.get("birim") or row.get("employee_birim"))
        status = _safe_str(row.get("status") or row.get("event_type")).lower()

        key = (ust_birim, birim)
        bucket = grouped[key]
        bucket["ust_birim"] = ust_birim
        bucket["birim"] = birim
        bucket["total"] += 1

        if status in {"tamamlandi", "completed"}:
            bucket["completed"] += 1
        elif status in {"taslak", "draft"}:
            bucket["draft"] += 1
        else:
            bucket["waiting"] += 1

    result = list(grouped.values())
    result.sort(key=lambda x: (-x["total"], x["ust_birim"].lower(), x["birim"].lower()))
    if top_n is not None:
        try:
            result = result[: max(0, int(top_n))]
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance_service.py")
    return result


def get_period_level_3_flags(
    period: Any | None = None,
    weight_config: Any | None = None,
) -> dict[str, Any]:
    """Eski çağrılar için güvenli köprü.

    Bazı route'lar ikinci argüman olarak weight_config nesnesi gönderiyor.
    Bunu period_id gibi yorumlamadan doğrudan modüler helper'a iletir.
    """
    return _get_period_level_3_flags_mod(period=period, weight_config=weight_config)


def is_informational_special_case(*args: Any, **kwargs: Any) -> bool:
    return _is_informational_special_case_mod(*args, **kwargs)


def build_assignment_log_summary(result: Any | None = None) -> dict[str, Any]:
    if isinstance(result, list):
        if result and _is_mapping_row(result[0]):
            return _legacy_assignment_log_summary(result)
        return _build_assignment_log_summary_mod(result)
    if isinstance(result, dict):
        return dict(result)
    return _build_assignment_log_summary_mod([])


def build_assignment_unit_summary(
    rows: list[Any] | None = None,
    *,
    top_n: int | None = None,
) -> list[dict[str, Any]]:
    rows = rows or []
    if rows and _is_mapping_row(rows[0]):
        return _legacy_assignment_unit_summary(rows, top_n=top_n)
    return _build_assignment_unit_summary_mod(rows, top_n=top_n)


def get_latest_assignment_generation_logs(*args: Any, **kwargs: Any) -> dict[str, Any]:
    period_id = None
    limit = kwargs.pop("limit", 200)
    employee_ids = kwargs.pop("employee_ids", None)

    if args:
        period_id = args[0]
        if len(args) > 1 and "limit" not in kwargs:
            limit = args[1]

    if period_id is None:
        active_period = get_active_period()
        period_id = getattr(active_period, "id", None)

    if period_id is None:
        return {
            "run_key": None,
            "created_at": None,
            "rows": [],
            "summary": _build_assignment_log_summary_mod([]),
            "severity_summary": {},
        }

    return _get_latest_assignment_generation_logs_mod(
        period_id=int(period_id),
        limit=max(1, int(limit or 200)),
        employee_ids=employee_ids,
    )


def generate_assignments_for_active_period(
    period_id: int | None = None,
    *args: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    """Tek yetkili görev üretim girişi.

    Böylece eski route'lar da güncel V2 senkronuna düşer:
    - admin kullanıcılar görev kapsamı dışında kalır
    - efektif amir / vekâlet zinciri devreye girer
    - 3. amir ve loglama modüler çekirdekten çalışır
    """
    actor_user_id = kwargs.pop("actor_user_id", None)
    return _generate_assignments_for_active_period_mod(
        period_id=period_id,
        actor_user_id=actor_user_id,
    )


__all__ = [
    "_safe_str",
    "_safe_float",
    "analyze_hierarchy_gaps",
    "analyze_hierarchy_rows",
    "build_assignment_generation_snapshot",
    "build_assignment_log_summary",
    "build_chain_health_snapshot",
    "build_performance_service_snapshot",
    "build_team_compare_snapshot",
    "build_assignment_unit_summary",
    "calculate_effective_weights",
    "calculate_preview_total_100",
    "generate_assignments_for_active_period",
    "get_active_period",
    "get_active_weight_config",
    "get_base_weight_map",
    "get_latest_assignment_generation_logs",
    "get_level_items_map",
    "get_period",
    "get_period_level_3_flags",
    "is_informational_special_case",
    "is_single_manager_case",
    "level_1_gave_any_three",
    "normalize_weight_inputs",
    "recalculate_all_evaluations",
    "requires_general_comment",
    "requires_level_2_comment_for_evaluation",
    "run_assignment_generation_with_snapshot",
    "save_evaluation_level",
    "validate_general_comment_requirements",
    "validate_score_value",
]