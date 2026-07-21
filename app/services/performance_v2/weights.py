from __future__ import annotations

import logging

from .dto import WeightPlan
from .rules import LevelMode, normalize_level_mode, normalize_weights, resolve_chain_policy

logger = logging.getLogger(__name__)


# BYS360_PHASE4_5_V2_WEIGHT_PLAN_OVERRIDE
def resolve_weight_plan(employee, period=None, resolved_chain=None) -> WeightPlan:  # type: ignore[override]
    policy = resolve_chain_policy(employee)
    level_mode = normalize_level_mode(period)

    if resolved_chain is None and employee is not None:
        try:
            from .chain import build_resolved_chain
            resolved_chain = build_resolved_chain(employee=employee, period=period)
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            resolved_chain = None

    if resolved_chain is not None:
        available_levels = {
            int(level)
            for level, payload in (getattr(resolved_chain, 'levels', {}) or {}).items()
            if getattr(payload, 'evaluator_id', None)
        }
    else:
        available_levels = set(policy.labels.keys())

    raw_weights = {
        1: float(getattr(period, 'level_1_weight', policy.default_weights.get(1, 50.0)) or 0),
        2: float(getattr(period, 'level_2_weight', policy.default_weights.get(2, 50.0)) or 0),
        3: float(getattr(period, 'level_3_weight', policy.default_weights.get(3, 0.0)) or 0),
    }
    source = 'period'
    if not period:
        raw_weights = dict(policy.default_weights)
        source = 'policy_default'

    try:
        from app.services.performance.third_supervisor_policy import (
            normalize_third_supervisor_weights,
            resolve_third_supervisor_weight_mode,
        )
        manager_3_present = 3 in available_levels
        weight_mode = resolve_third_supervisor_weight_mode(period, manager_3_id=3 if manager_3_present else None)
        include_third = bool(weight_mode.get('include_weight'))
        if not include_third:
            available_levels.discard(3)
        normalized = normalize_third_supervisor_weights(
            raw_weights,
            enabled_levels=available_levels or {1, 2},
            include_third=include_third,
        )
        level_mode_value = 'scoring' if include_third else ('comment_only' if weight_mode.get('enabled') else 'off')
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        if level_mode != LevelMode.SCORE_ENABLED:
            raw_weights[3] = 0.0
            available_levels.discard(3)
        normalized = normalize_weights(raw_weights, enabled_levels=available_levels or {1, 2})
        level_mode_value = level_mode.value

    return WeightPlan(
        level_weights=normalized,
        normalized_total=round(sum(normalized.values()), 2),
        level_mode=level_mode_value,
        source=source,
    )

