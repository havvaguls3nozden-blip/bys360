from __future__ import annotations

from collections.abc import Iterable
from typing import Any

INFO_EXCEPTION_RULES = {
    "special_presidency_single_manager",
    "top_office_node_exception",
}


def _s(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _get(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


def _extract_row(row: Any) -> dict[str, Any]:
    return {
        "full_name": _get(row, "full_name"),
        "ad": _get(row, "ad"),
        "soyad": _get(row, "soyad"),
        "sicil_no": _get(row, "sicil_no"),
        "role": _get(row, "role"),
        "birim": _get(row, "birim"),
        "ust_birim": _get(row, "ust_birim"),
        "manager_1": _s(_get(row, "manager_1") or _get(row, "yonetici_sicil")),
        "manager_2": _s(_get(row, "manager_2") or _get(row, "ikinci_yonetici_sicil")),
        "manager_3": _s(_get(row, "manager_3") or _get(row, "ucuncu_yonetici_sicil")),
        "issues": _s(_get(row, "issues")),
        "warnings": _s(_get(row, "warnings")),
        "exception_rule": _s(_get(row, "exception_rule")),
        "effective_severity": _s(_get(row, "effective_severity")).lower(),
    }


def normalize_hierarchy_row(row: Any) -> dict[str, Any]:
    item = _extract_row(row)
    if item["exception_rule"] in INFO_EXCEPTION_RULES:
        item["effective_severity"] = "info"
        item["slot_issues"] = []
    else:
        issues: list[str] = []
        if not item["manager_1"]:
            issues.append("1. amir eksik veya pasif")
        if not item["manager_2"] and _s(item["role"]).lower() != "baskan_yardimcisi":
            issues.append("2. amir eksik veya pasif")
        item["slot_issues"] = issues
        if issues:
            item["effective_severity"] = "critical"
        elif item["warnings"]:
            item["effective_severity"] = "warning"
        else:
            item["effective_severity"] = item["effective_severity"] or "success"
    return item


def build_hierarchy_health_rows(rows: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in (rows or []):
        item = normalize_hierarchy_row(row)
        if item["effective_severity"] in {"critical", "warning"}:
            item["issues"] = ", ".join(item.get("slot_issues") or [])
            result.append(item)
    return result


def summarize_hierarchy_health(rows: Iterable[Any] | None = None) -> dict[str, int]:
    normalized = [normalize_hierarchy_row(r) for r in (rows or [])]
    return {
        "total": len(normalized),
        "critical": sum(1 for r in normalized if r["effective_severity"] == "critical"),
        "warning": sum(1 for r in normalized if r["effective_severity"] == "warning"),
        "info": sum(1 for r in normalized if r["effective_severity"] == "info"),
        "success": sum(1 for r in normalized if r["effective_severity"] == "success"),
        "missing_manager_1": sum(1 for r in normalized if any("1. amir" in issue for issue in (r.get("slot_issues") or []))),
        "warning_records": sum(1 for r in normalized if r["effective_severity"] == "warning"),
        "third_manager_flow_count": sum(1 for r in normalized if r.get("manager_3")),
        "two_manager_flow_count": sum(1 for r in normalized if r.get("manager_1") and r.get("manager_2") and not r.get("manager_3")),
        "single_manager_count": sum(1 for r in normalized if r.get("manager_1") and not r.get("manager_2")),
        "presidency_level_count": sum(1 for r in normalized if _s(r.get("birim")).upper() == "BAŞKANLIK" or _s(r.get("ust_birim")).upper() == "BAŞKANLIK"),
        "full_chain_count": sum(1 for r in normalized if not (r.get("slot_issues") or [])),
    }


build_health_rows = build_hierarchy_health_rows
build_hierarchy_rows = build_hierarchy_health_rows
get_visible_hierarchy_health_rows = build_hierarchy_health_rows
get_hierarchy_health_summary = summarize_hierarchy_health
summarize_chain_heat = summarize_hierarchy_health
build_zincir_sicakligi_summary = summarize_hierarchy_health