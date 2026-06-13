from __future__ import annotations

from app.refactor.final_quality_security_compliance_contract import (
    FINAL_QUALITY_FAZ4_VERSION,
    PERSONAL_DATA_FLOWS,
    SECURITY_AUDIT_EVIDENCE,
    SECURITY_COMPLIANCE_CONTROLS,
    SECURITY_FORBIDDEN_RUNTIME_ACTIONS,
    get_final_quality_faz4_summary,
    get_personal_data_flow_keys,
    get_security_control_keys,
)


def test_security_compliance_controls_cover_kvkk_ts27001_iso42001_and_ai_governance() -> None:
    keys = set(get_security_control_keys())
    assert "kvkk_personal_data_minimization" in keys
    assert "csrf_session_cookie_hardening" in keys
    assert "audit_log_traceability" in keys
    assert "ai_governance_redaction" in keys
    assert "release_artifact_hygiene" in keys
    assert "live_backbone_access_boundaries" in keys

    refs = " ".join(ref for control in SECURITY_COMPLIANCE_CONTROLS for ref in control.standard_refs)
    assert "KVKK" in refs
    assert "TS 27001" in refs
    assert "ISO 42001" in refs


def test_personal_data_flows_are_bound_to_live_backbone_tables_and_audit() -> None:
    assert get_personal_data_flow_keys() == (
        "personnel_identity_flow",
        "performance_evaluation_flow",
        "leave_delegation_flow",
        "communication_feedback_flow",
        "ai_decision_support_flow",
    )
    for flow in PERSONAL_DATA_FLOWS:
        assert flow.personal_data_scope
        assert flow.storage_or_log_tables
        assert "audit" in " ".join(flow.protection_controls + (flow.audit_note,)).lower()


def test_security_audit_evidence_keeps_required_release_markers() -> None:
    markers = {evidence.release_gate_marker for evidence in SECURITY_AUDIT_EVIDENCE}
    assert "CLEAN_LIVE_RELEASE_GATE_OK" in markers
    assert "CLAUDE_10_10_GATE_OK" in markers
    assert "FINAL_QUALITY_FAZ3_CHAIN_OK" in markers
    assert "FINAL_QUALITY_FAZ4_CHAIN_OK" in markers


def test_faz4_summary_declares_no_runtime_mutation_or_external_network() -> None:
    summary = get_final_quality_faz4_summary()
    assert summary["version"] == FINAL_QUALITY_FAZ4_VERSION
    assert summary["security_control_count"] >= 6
    assert summary["personal_data_flow_count"] >= 5
    assert summary["runtime_mutation"] is False
    assert summary["database_migration"] is False
    assert summary["external_network"] is False


def test_security_forbidden_runtime_actions_are_named_as_policy_not_code_calls() -> None:
    assert "runtime_blueprint_registration" in SECURITY_FORBIDDEN_RUNTIME_ACTIONS
    assert "database_schema_mutation" in SECURITY_FORBIDDEN_RUNTIME_ACTIONS
    assert "external_network_call" in SECURITY_FORBIDDEN_RUNTIME_ACTIONS
    assert "secret_value_hardcoding" in SECURITY_FORBIDDEN_RUNTIME_ACTIONS
