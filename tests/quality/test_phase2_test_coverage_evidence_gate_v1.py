from __future__ import annotations

from pathlib import Path

from scripts.quality.bys360_phase2_test_coverage_evidence_gate_v1 import run_checks


def test_phase2_test_coverage_evidence_gate_v1() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_checks(root, write_report=False)

    assert result["evidence_gate_ok"] is True
    assert result["git_clean_ok"] is True
    assert result["required_files_ok"] is True
    assert result["reports_ok"] is True
