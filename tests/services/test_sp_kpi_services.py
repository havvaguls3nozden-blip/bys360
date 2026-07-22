"""BYS360 Maintenance 10E - SP servis unit testleri."""
from __future__ import annotations

from decimal import Decimal


def test_shared_kpi_completion_rate_boundaries():
    from app.services.kpi_utils import calculate_completion_rate

    assert calculate_completion_rate(100, 82) == Decimal("82.00")
    assert calculate_completion_rate(0, 82) == Decimal("0.00")
    assert calculate_completion_rate(-100, 82) == Decimal("0.00")
    assert calculate_completion_rate(100, -5) == Decimal("0.00")
    assert calculate_completion_rate(100, 150) == Decimal("150.00")
    assert calculate_completion_rate(100, 150, cap_at_100=True) == Decimal("100.00")


def test_kpi_service_status_classification():
    from app.modules.strategic_performance.services.kpi_service import (
        classify_kpi_status,
        enrich_target,
    )

    assert classify_kpi_status(95)["status_label"] == "Tamamlandı"
    assert classify_kpi_status(75)["status_label"] == "Devam Ediyor"
    assert classify_kpi_status(55)["status_label"] == "Riskli"
    assert classify_kpi_status(10)["status_label"] == "Kritik"

    enriched = enrich_target({"target_value": 200, "current_value": 100})
    assert enriched["completion_rate"] == 50.0
    assert enriched["status"] == "at_risk"


def test_dashboard_service_uses_shared_kpi_cap():
    from app.modules.strategic_performance_dashboard.services.dashboard_service import (
        calculate_completion_rate,
        resolve_kpi_status,
    )

    assert calculate_completion_rate(100, 150) == 100.0
    assert resolve_kpi_status(90) == "Tamamlandı"
    assert resolve_kpi_status(49) == "Kritik"


def test_target_service_prepare_update_contract():
    from app.modules.strategic_performance.services.target_service import prepare_target_update

    payload = prepare_target_update(100, 72)
    assert payload["completion_rate"] == Decimal("72.00")
    assert payload["status"] == "ongoing"
    assert payload["risk_level"] == "normal"


def test_competency_payload_normalization():
    from app.modules.strategic_performance.services.competency_service import competency_payload

    payload = competency_payload("Teknik", "  Teknik   Uzmanlık  ", "Açıklama")
    assert payload["competency_name"] == "Teknik Uzmanlık"
    assert payload["active"] is True
