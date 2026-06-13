from __future__ import annotations

from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FEEDBACK_ROUTES = PROJECT_ROOT / "app" / "communication" / "feedback_routes.py"
FEEDBACK_SERVICE = PROJECT_ROOT / "app" / "services" / "feedback_service.py"


@pytest.mark.source_smoke
def test_feedback_routes_contains_core_handlers() -> None:
    source = FEEDBACK_ROUTES.read_text(encoding="utf-8")
    expected = [
        "def feedback_dashboard",
        "def feedback_pulse",
        "def feedback_campaigns",
        "def feedback_campaign_detail",
        "def feedback_results",
        "def feedback_actions",
        "def feedback_manager",
        "def feedback_campaign_manage",
        "def feedback_results_export",
    ]
    missing = [item for item in expected if item not in source]
    assert missing == [], f"Eksik feedback handler tanımları: {missing}"


@pytest.mark.source_smoke
def test_feedback_service_contains_phase6_foundations() -> None:
    source = FEEDBACK_SERVICE.read_text(encoding="utf-8")
    expected = [
        "def save_pulse_entry",
        "def get_today_pulse_entry",
        "def create_campaign_from_form",
        "def submit_campaign_answers",
        "def build_campaign_results",
        "def build_dashboard_data",
        "def build_manager_summary",
    ]
    missing = [item for item in expected if item not in source]
    assert missing == [], f"Eksik feedback servis fonksiyonları: {missing}"


@pytest.mark.uat
def test_feedback_menu_contract_notes_present() -> None:
    source = FEEDBACK_ROUTES.read_text(encoding="utf-8")
    for menu_key in [
        "feedback_dashboard",
        "feedback_pulse",
        "feedback_campaigns",
        "feedback_results",
        "feedback_actions",
        "feedback_manager",
        "feedback_admin",
    ]:
        assert menu_key in source, f"Menu anahtarı görünmüyor: {menu_key}"
