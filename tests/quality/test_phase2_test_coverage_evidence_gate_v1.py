from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import scripts.quality.bys360_phase2_test_coverage_evidence_gate_v1 as gate

pytestmark = pytest.mark.ci_safe

ROOT = Path(__file__).resolve().parents[2]

# BYS360 Phase2E root-cause fix (2026-07-26): "git status --short" gerçek
# çalışma ağacına bağımlıydı, bu yüzden test her legitim kalite kanıt
# artefaktı veya alakasız geçici değişiklikle kırılıyordu. Bu testler artık
# `_run`'ı monkeypatch ile enjekte edilen git status metniyle değiştirip
# gerçek `run_checks`/`_classify_git_status` mantığını deterministik
# senaryolar üzerinden doğruluyor; canlı çalışma ağacının o an temiz olması
# gerekmiyor.
ARTIFACT_ONLY_STATUS = (
    "?? .coverage\n"
    "?? reports/quality/BYS360_CAMPAIGN1B_TRUTHFUL_QUALITY_GATES_CLOSURE_DELIVERY_REPORT.docx\n"
    "?? reports/quality/BYS360_CAMPAIGN1_TRUTHFUL_QUALITY_GATES_DELIVERY_REPORT.docx\n"
    "?? reports/quality/BYS360_SECRET_REPO_GATE_V1_REPORT.json\n"
    "?? reports/quality/coverage.xml\n"
)


def _fake_git_run(status_stdout: str) -> Any:
    def _fake_run(cmd: list[str], root: Path) -> dict[str, Any]:
        if cmd[:2] == ["git", "status"]:
            stdout = status_stdout
        elif cmd[:2] == ["git", "log"]:
            stdout = "abc1234 fake commit for test"
        else:
            raise AssertionError(f"unexpected command in test double: {cmd}")
        return {"cmd": cmd, "returncode": 0, "stdout": stdout, "stderr": "", "ok": True}

    return _fake_run


def test_artifact_only_scenario_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "_run", _fake_git_run(ARTIFACT_ONLY_STATUS))

    result = gate.run_checks(ROOT, write_report=False)

    assert result["git_clean_ok"] is True
    assert result["required_files_ok"] is True
    assert result["reports_ok"] is True
    assert result["evidence_gate_ok"] is True

    classification = result["git_status_classification"]
    assert classification["unexpected_files"] == []
    assert classification["allowed_artifacts"] == classification["untracked_files"]


def test_clean_status_scenario_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "_run", _fake_git_run(""))

    result = gate.run_checks(ROOT, write_report=False)

    assert result["git_clean_ok"] is True
    assert result["evidence_gate_ok"] is True
    assert result["git_status_classification"]["unexpected_files"] == []


def test_rejects_unexpected_untracked_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "_run", _fake_git_run("?? scratch.txt\n"))

    result = gate.run_checks(ROOT, write_report=False)

    assert result["git_clean_ok"] is False
    assert result["evidence_gate_ok"] is False
    assert "scratch.txt" in result["git_status_classification"]["unexpected_files"]


def test_rejects_unrelated_tracked_change(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "_run", _fake_git_run(" M app/some_unrelated_module.py\n"))

    result = gate.run_checks(ROOT, write_report=False)

    assert result["git_clean_ok"] is False
    assert result["evidence_gate_ok"] is False
    assert "app/some_unrelated_module.py" in result["git_status_classification"]["unexpected_files"]


def test_rejects_json_outside_whitelist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "_run", _fake_git_run("?? reports/quality/SOME_OTHER_REPORT.json\n"))

    result = gate.run_checks(ROOT, write_report=False)

    assert result["git_clean_ok"] is False
    assert "reports/quality/SOME_OTHER_REPORT.json" in result["git_status_classification"]["unexpected_files"]


def test_rejects_docx_not_matching_delivery_report_pattern(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "_run", _fake_git_run("?? reports/quality/RANDOM_NOTES.docx\n"))

    result = gate.run_checks(ROOT, write_report=False)

    assert result["git_clean_ok"] is False
    assert "reports/quality/RANDOM_NOTES.docx" in result["git_status_classification"]["unexpected_files"]


def test_ignored_files_are_reported_but_do_not_fail_git_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    status = "!! __pycache__/\n" + ARTIFACT_ONLY_STATUS
    monkeypatch.setattr(gate, "_run", _fake_git_run(status))

    result = gate.run_checks(ROOT, write_report=False)

    classification = result["git_status_classification"]
    assert "__pycache__/" in classification["ignored_files"]
    assert "__pycache__/" not in classification["unexpected_files"]
    assert result["git_clean_ok"] is True
    assert result["evidence_gate_ok"] is True


def test_own_report_paths_are_still_exempt(monkeypatch: pytest.MonkeyPatch) -> None:
    status = (
        " M reports/architecture/BYS360_PHASE2_TEST_COVERAGE_EVIDENCE_GATE_V1_REPORT.json\n"
        "?? reports/architecture/BYS360_PHASE2_TEST_COVERAGE_EVIDENCE_GATE_V1_REPORT.md\n"
    )
    monkeypatch.setattr(gate, "_run", _fake_git_run(status))

    result = gate.run_checks(ROOT, write_report=False)

    assert result["git_clean_ok"] is True
    assert result["git_status_classification"]["unexpected_files"] == []
