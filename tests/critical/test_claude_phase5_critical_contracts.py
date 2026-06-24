from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def _defs(rel: str) -> set[str]:
    tree = ast.parse(_text(rel), filename=rel)
    return {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def test_live_settings_contract_is_covered():
    source = _text("app/models/settings_models.py")
    for table in [
        "system_settings",
        "module_settings",
        "settings_change_logs",
        "role_menu_defaults",
        "unit_menu_profiles",
    ]:
        assert f'__tablename__ = "{table}"' in source

    service_defs = _defs("app/services/settings_service.py")
    for name in [
        "ensure_settings_phase1_seeded",
        "build_effective_user_menu_context",
        "save_system_settings_from_form",
        "save_module_settings_from_form",
        "rollback_settings_change",
    ]:
        assert name in service_defs


def test_performance_manager_constitution_contract_is_covered():
    source = _text("app/services/performance/manager_rule_constitution.py")
    for token in [
        "group_staff",
        "coordinator",
        "group_manager",
        "hukuk_single_manager",
        "direct_president_titles",
        "flow",
    ]:
        assert token in source


def test_performance_visibility_and_chain_fields_remain_present():
    source = _text("app/models/performance_models.py")
    for token in [
        "results_published",
        "enable_level_3_scoring",
        "level_1_completed",
        "level_2_completed",
        "level_3_completed",
        "level_2_seen_level_1_at",
    ]:
        assert token in source


def test_feedback_pulse_campaign_contract_is_covered():
    source = _text("app/models/feedback_models.py")
    for table in [
        "feedback_campaigns",
        "feedback_questions",
        "feedback_submissions",
        "feedback_answers",
        "feedback_pulse_entries",
    ]:
        assert f'__tablename__ = "{table}"' in source

    service_defs = _defs("app/services/feedback_service.py")
    for name in ["list_visible_campaigns_for_user", "submit_campaign_answers", "build_pulse_analytics", "build_campaign_results"]:
        assert name in service_defs


def test_message_and_survey_contract_is_covered():
    message_models = _text("app/models/communication_models.py")
    for table in ["messages", "message_threads", "message_thread_participants", "message_attachments"]:
        assert f'__tablename__ = "{table}"' in message_models

    service_defs = _defs("app/services/message_service.py")
    for name in ["get_or_create_direct_thread", "save_message_attachment", "get_visible_surveys_for_user"]:
        assert name in service_defs


def test_ai_decision_support_contract_is_covered():
    source = _text("app/models/ai_models.py")
    for table in ["ai_feedback_logs", "ai_recommendations", "ai_redaction_rules", "ai_request_logs", "ai_summary_cache"]:
        assert f'__tablename__ = "{table}"' in source

    service_defs = _defs("app/services/decision_support_service.py")
    for name in ["build_dashboard_signal_context", "build_task_signal_context", "build_personnel_signal_context"]:
        assert name in service_defs


def test_security_and_mail_contracts_are_covered():
    security_candidates = [
        ROOT / "app" / "security" / "captcha_guard.py",
        ROOT / "app" / "security.py",
        ROOT / "app" / "services" / "security_hardening_service.py",
    ]
    assert any(path.exists() for path in security_candidates)

    mail_defs = _defs("app/services/mail_service.py")
    for name in ["get_smtp_settings", "send_email", "send_bulk_assignment_reminders", "build_mail_system_health_snapshot"]:
        assert name in mail_defs


def test_phase5_quality_gate_exists():
    gate = ROOT / "scripts" / "quality" / "check_critical_services_phase5_gate.py"
    assert gate.exists()
    source = gate.read_text(encoding="utf-8")
    assert "LIVE_CONTRACTS" in source
    assert "CRITICAL_TEST_PATTERNS" in source
    assert "BYS360 Maintenance Faz 5" in source
