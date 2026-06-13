from pathlib import Path


def test_phase7_contract_module_is_complete():
    from app.services.go_live.final_quality_contracts import (
        FINAL_GATE_REQUIRED_PATHS,
        LIVE_CORE_TABLES,
        LIVE_MODULE_FAMILIES,
        PREVIOUS_CLAUDE_GATES,
    )

    assert "users" in LIVE_CORE_TABLES
    assert "performance_evaluations" in LIVE_CORE_TABLES
    assert "surveys" in LIVE_CORE_TABLES
    assert "ai_recommendations" in LIVE_CORE_TABLES
    assert "performans_yonetimi" in LIVE_MODULE_FAMILIES
    assert "ai_karar_destek" in LIVE_MODULE_FAMILIES
    assert "app/error_handlers.py" in FINAL_GATE_REQUIRED_PATHS
    assert "app/services/settings/catalog.py" in FINAL_GATE_REQUIRED_PATHS
    assert any(gate.phase == "Faz 6" for gate in PREVIOUS_CLAUDE_GATES)


def test_phase7_quality_script_exists():
    assert Path("scripts/quality/check_claude_phase7_final_gate.py").exists()
    assert Path("scripts/windows/claude_phase7_final_quality.ps1").exists()
