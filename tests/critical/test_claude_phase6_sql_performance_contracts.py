from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(rel: str, name: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_phase6_index_catalog_covers_live_core_tables():
    contracts = _load("app/services/query_health/index_contracts.py", "phase6_contracts_test")
    tables = {item.table for item in contracts.RECOMMENDED_INDEXES}
    for table in [
        "users",
        "system_settings",
        "module_settings",
        "leave_requests",
        "delegation_assignments",
        "evaluation_assignments",
        "performance_evaluations",
        "feedback_submissions",
        "feedback_pulse_entries",
        "message_threads",
        "messages",
        "surveys",
        "survey_responses",
        "ai_request_logs",
        "ai_summary_cache",
    ]:
        assert table in tables


def test_phase6_sql_generation_is_create_index_only():
    contracts = _load("app/services/query_health/index_contracts.py", "phase6_contracts_sql_test")
    sql = contracts.build_postgresql_index_sql()
    assert "CREATE INDEX IF NOT EXISTS" in sql
    for unsafe in ["DROP ", "TRUNCATE ", "DELETE ", "UPDATE ", "ALTER TABLE"]:
        assert unsafe not in sql.upper()


def test_phase6_query_guard_can_scan_without_db():
    guard = _load("app/services/query_health/static_query_guard.py", "phase6_guard_test")
    findings = guard.collect_query_risk_findings(ROOT)
    assert isinstance(findings, list)
    assert isinstance(guard.summarize_findings(findings), dict)


def test_phase6_quality_gate_exists():
    gate = ROOT / "scripts" / "quality" / "check_sql_performance_phase6_gate.py"
    assert gate.exists()
    source = gate.read_text(encoding="utf-8")
    assert "REQUIRED_TABLES" in source
    assert "phase6_index_recommendations.sql" in source
