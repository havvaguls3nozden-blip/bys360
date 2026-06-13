# -*- coding: utf-8 -*-
"""BYS360 Faz 11 dönem/kapsam/görev üretimi servis köprüsü."""
from __future__ import annotations

from typing import Any, Iterable

from app.services.performance.phase11_period_scope_assignment_center import (
    BYS360_PERFORMANCE_COMPLETION_PHASE11_VERSION,
    phase11_assignment_precheck,
    phase11_clean_text,
    phase11_filter_personnel_by_scope,
    phase11_period_scope_contract,
    phase11_safe_assignment_rows,
    phase11_validate_period_scope,
)

BYS360_PERFORMANCE_COMPLETION_PHASE11_SERVICE_BRIDGE = True


def validate_period_scope(payload: dict[str, Any]) -> dict[str, Any]:
    return phase11_validate_period_scope(payload).as_dict()


def build_assignment_precheck(period_payload: dict[str, Any], personnel_rows: Iterable[Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    return phase11_assignment_precheck(period_payload, personnel_rows or [], **kwargs).as_dict()


def build_safe_assignment_rows(personnel_rows: Iterable[Any], scope: dict[str, Any]) -> list[dict[str, Any]]:
    return phase11_safe_assignment_rows(personnel_rows, scope)


def clean_period_scope_text(value: Any) -> str:
    return phase11_clean_text(value)


def get_period_scope_contract() -> dict[str, Any]:
    return phase11_period_scope_contract()
