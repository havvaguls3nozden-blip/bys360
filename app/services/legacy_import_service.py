from __future__ import annotations



from typing import Any

from sqlalchemy import func

from app.models import OrganizationUnit, User


def legacy_norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def legacy_norm_lower(value: Any) -> str:
    return legacy_norm(value).lower()


def legacy_truthy(value: Any) -> bool:
    return legacy_norm_lower(value) in {"1", "true", "evet", "yes", "on", "aktif"}


def legacy_header_index(header_row) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for idx, cell in enumerate(header_row):
        key = legacy_norm_lower(cell)
        if key:
            mapping[key] = idx
    return mapping


def legacy_pick(row, header_index: dict[str, int], *names: str, default: str = "") -> str:
    for name in names:
        idx = header_index.get(legacy_norm_lower(name))
        if idx is not None and idx < len(row):
            return legacy_norm(row[idx])
    return default


def resolve_legacy_employee(row_data: dict[str, Any]):
    sicil_no = legacy_norm(row_data.get("sicil_no"))
    ad_soyad = legacy_norm(row_data.get("employee_name_raw"))

    employee = None
    if sicil_no:
        employee = User.query.filter_by(sicil_no=sicil_no).first()

    if not employee and ad_soyad:
        parts = ad_soyad.split()
        if len(parts) >= 2:
            ad = parts[0]
            soyad = " ".join(parts[1:])
            employee = User.query.filter(
                func.lower(User.ad) == ad.lower(),
                func.lower(User.soyad) == soyad.lower(),
            ).first()

    return employee


def resolve_unit_for_legacy(birim: str, ust_birim: str):
    birim = legacy_norm(birim)
    ust_birim = legacy_norm(ust_birim)
    if not birim:
        return None

    candidates = OrganizationUnit.query.filter(
        func.lower(OrganizationUnit.name) == birim.lower()
    ).all()

    if not candidates:
        return None

    if not ust_birim:
        return candidates[0]

    for unit in candidates:
        parent_name = legacy_norm(unit.parent.name) if unit.parent else ""
        if parent_name.lower() == ust_birim.lower():
            return unit

    return candidates[0]


def collect_extra_payload(row_data: dict[str, Any]) -> dict[str, Any]:
    known = {
        "sicil_no",
        "employee_name_raw",
        "birim_raw",
        "ust_birim_raw",
        "final_total_100",
        "level_1_total_100",
        "level_2_total_100",
        "level_3_total_100",
        "manager_1_name",
        "manager_2_name",
        "manager_3_name",
        "manager_1_sicil",
        "manager_2_sicil",
        "manager_3_sicil",
        "comment_1",
        "comment_2",
        "comment_3",
        "status",
    }
    return {k: v for k, v in row_data.items() if k not in known and v not in (None, "")}


__all__ = [
    "collect_extra_payload",
    "legacy_header_index",
    "legacy_norm",
    "legacy_norm_lower",
    "legacy_pick",
    "legacy_truthy",
    "resolve_legacy_employee",
    "resolve_unit_for_legacy",
]