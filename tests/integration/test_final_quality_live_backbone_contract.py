from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# BYS360_SPRINT2_LEGACY_INTEGRATION_SCOPE_V8
pytestmark = [pytest.mark.legacy_integration, pytest.mark.realdb]
ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "app" / "refactor" / "final_quality_live_backbone_contract.py"


def load_contract_module():
    spec = importlib.util.spec_from_file_location("final_quality_live_backbone_contract", CONTRACT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_live_backbone_contract_covers_all_current_live_areas() -> None:
    module = load_contract_module()
    assert module.get_live_backbone_keys() == (
        "identity_authorization_settings",
        "personnel_organization",
        "performance_management",
        "leave_delegation",
        "communication_survey_feedback",
        "support_center",
        "ai_decision_support",
        "home_weather_daily_summary",
    )


def test_live_backbone_contract_contains_required_table_families() -> None:
    module = load_contract_module()
    area_tables = {area.key: set(area.table_names) for area in module.LIVE_BACKBONE_AREAS}
    assert {"users", "system_settings", "audit_logs"}.issubset(area_tables["identity_authorization_settings"])
    assert {"organization_units", "employee_org_assignment_history"}.issubset(area_tables["personnel_organization"])
    assert {"performance_periods", "evaluation_assignments", "performance_evaluations"}.issubset(area_tables["performance_management"])
    assert {"personnel_leaves", "delegation_assignments"}.issubset(area_tables["leave_delegation"])
    assert {"messages", "message_threads", "surveys", "survey_responses"}.issubset(area_tables["communication_survey_feedback"])
    assert {"support_tickets", "support_ticket_messages"}.issubset(area_tables["support_center"])
    assert {"ai_request_logs", "ai_recommendations", "ai_summary_cache"}.issubset(area_tables["ai_decision_support"])


def test_critical_integration_flows_are_locked() -> None:
    module = load_contract_module()
    flows = {flow.key: flow for flow in module.CRITICAL_INTEGRATION_FLOWS}
    assert "personnel_to_performance_assignment" in flows
    assert "leave_delegation_to_performance_task" in flows
    assert "performance_publish_to_personnel_visibility" in flows
    assert "ai_decision_to_audit_logs" in flows
    assert flows["performance_publish_to_personnel_visibility"].risk_guard == "İK/Admin yayınlamadan personel sonucu göremez."
    assert "vekil" in flows["leave_delegation_to_performance_task"].risk_guard.lower()


def test_release_evidence_contracts_are_present_and_non_mutating() -> None:
    module = load_contract_module()
    summary = module.get_final_quality_faz3_summary()
    assert summary["backbone_area_count"] == 8
    assert summary["integration_flow_count"] >= 6
    assert summary["release_evidence_count"] >= 4
    assert summary["runtime_mutation"] is False
    assert summary["database_migration"] is False


def test_contract_module_has_no_runtime_side_effects() -> None:
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    forbidden = [
        "register_blueprint(",
        "db.session" + ".commit(",
        ".create" + "_all(",
        ".drop" + "_all(",
        "ALTER " + "TABLE",
        "DROP " + "TABLE",
        "requests" + ".get(",
        "url" + "open(",
    ]
    for snippet in forbidden:
        assert snippet not in text
