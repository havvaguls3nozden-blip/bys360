
"""Performance route context helpers.

Phase 2 amaci, period/agirlik secimi gibi route icinde tekrar eden sorgu ve
coercion mantigini tek bir servis yuzeyine almak. Bu dosya business rule
uretmez; mevcut davranisi koruyarak route katmanini inceltir.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.extensions import db
from app.models import PerformancePeriod, PerformanceWeightConfig


def list_performance_periods() -> list[PerformancePeriod]:
    return (
        PerformancePeriod.query
        .order_by(PerformancePeriod.start_date.desc(), PerformancePeriod.id.desc())
        .all()
    )


def coerce_period_id(source: Any, key: str = "period_id") -> int | None:
    raw = source
    if isinstance(source, Mapping):
        getter = getattr(source, 'get', None)
        if callable(getter):
            try:
                typed = getter(key, type=int)
            except TypeError:
                typed = getter(key)
            if typed not in (None, ""):
                try:
                    return int(typed)
                except (TypeError, ValueError):
                    return None
            return None
    if raw in (None, ""):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def get_selected_period(period_id: int | None = None, *, fallback_to_active: bool = True) -> PerformancePeriod | None:
    selected = db.session.get(PerformancePeriod, period_id) if period_id else None
    if selected or not fallback_to_active:
        return selected
    return (
        PerformancePeriod.query
        .filter_by(is_active=True)
        .order_by(PerformancePeriod.id.desc())
        .first()
    )


def get_weight_config_for_period(period: PerformancePeriod | None) -> PerformanceWeightConfig | None:
    if period:
        row = (
            PerformanceWeightConfig.query
            .filter_by(period_id=period.id, is_active=True)
            .order_by(PerformanceWeightConfig.id.desc())
            .first()
        )
        if row:
            return row
    return (
        PerformanceWeightConfig.query
        .filter_by(is_active=True)
        .order_by(PerformanceWeightConfig.id.desc())
        .first()
    )


def build_period_weight_context(source: Any = None, *, period_id: int | None = None, fallback_to_active: bool = True) -> dict[str, Any]:
    resolved_period_id = period_id if period_id is not None else coerce_period_id(source)
    selected_period = get_selected_period(resolved_period_id, fallback_to_active=fallback_to_active)
    if selected_period and not resolved_period_id:
        resolved_period_id = selected_period.id
    periods = list_performance_periods()
    weight_config = get_weight_config_for_period(selected_period)
    return {
        'periods': periods,
        'selected_period_id': resolved_period_id,
        'selected_period': selected_period,
        'weight_config': weight_config,
    }


__all__ = [
    'build_period_weight_context',
    'coerce_period_id',
    'get_selected_period',
    'get_weight_config_for_period',
    'list_performance_periods',
]