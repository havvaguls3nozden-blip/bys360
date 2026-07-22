"""
BYS360 SP Dashboard Service
KPI, hedef, yetkinlik ve öz değerlendirme özetlerini güvenli şekilde üretir.
"""
from __future__ import annotations

from typing import Any

from app.services.kpi_utils import (
    calculate_completion_rate as _calculate_completion_rate_decimal,
)
from app.services.kpi_utils import (
    classify_kpi_status,
)
from app.services.kpi_utils import (
    to_decimal as _to_decimal,
)

# BYS360_MAINTENANCE_10E_DASHBOARD_SERVICE_USES_SHARED_KPI_UTILS


def _safe_float(value: Any, default: float = 0.0) -> float:
    decimal_value = _to_decimal(value)
    return float(decimal_value) if decimal_value is not None else default


def calculate_completion_rate(target_value: Any, current_value: Any) -> float:
    """Dashboard kartları için 100 üstünü sınırlayan tamamlanma oranı."""
    return float(_calculate_completion_rate_decimal(target_value, current_value, cap_at_100=True))


def resolve_kpi_status(rate: Any) -> str:
    return classify_kpi_status(rate)["status_label"]


def build_dashboard_summary(db_session: Any = None, current_user: Any = None) -> dict[str, Any]:
    return {
        "total_targets": 0,
        "completed_targets": 0,
        "risky_targets": 0,
        "critical_targets": 0,
        "average_completion": 0,
        "ai_notes": [
            "KPI ve hedef verileri stratejik performans omurgasına bağlandı.",
            "Riskli hedefler gerçek veri oluştuğunda burada özetlenecek.",
            "AI karar vermez; yalnızca yetki kontrollü analiz ve dikkat notu üretir.",
        ],
    }


def build_role_scope_label(current_user: Any = None) -> str:
    role = getattr(current_user, "role", None) or getattr(current_user, "role_name", None) or ""
    role = str(role).lower()
    if "başkan" in role or "baskan" in role or "admin" in role:
        return "Kurum Geneli"
    if "grup" in role:
        return "Grup Kapsamı"
    if "koordinat" in role:
        return "Koordinasyon Kapsamı"
    return "Kendi Kapsamım"
