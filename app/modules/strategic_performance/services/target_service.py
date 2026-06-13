"""BYS360 SP-1A hedef yönetimi servis iskeleti."""
from .kpi_service import calculate_completion_rate, classify_kpi_status


def prepare_target_update(target_value, current_value):
    rate = calculate_completion_rate(target_value, current_value)
    state = classify_kpi_status(rate)
    return {
        "completion_rate": rate,
        "status": state["status"],
        "risk_level": state["risk_level"],
    }
