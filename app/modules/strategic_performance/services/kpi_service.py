"""BYS360 SP KPI hesaplama servisi."""
from __future__ import annotations

from app.services.kpi_utils import calculate_completion_rate, classify_kpi_status, to_decimal as _to_decimal

# BYS360_CLAUDE_10E_KPI_SERVICE_USES_SHARED_UTILS


def enrich_target(target):
    """Model veya dict hedef kaydını hesaplanmış KPI bilgisiyle zenginleştirir."""
    getter = target.get if isinstance(target, dict) else lambda key, default=None: getattr(target, key, default)
    rate = calculate_completion_rate(getter("target_value"), getter("current_value"))
    state = classify_kpi_status(rate)
    return {"completion_rate": float(rate), **state}
