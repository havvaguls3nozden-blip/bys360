"""BYS360 Phase 6 dependency-audit closure -- PASS/FAIL/BLOCKED status contract.

Tests the real classification and policy functions in
``scripts/quality/bys360_score100_quality_gate_v1.py``:
``classify_dependency_audit_result``, ``resolve_dependency_audit_policy``,
and the Strict/Diagnostic gate-enforcement path in ``main()``.

No real pip-audit subprocess or network call is made anywhere in this file:
BLOCKED/FAIL/PASS outcomes are simulated deterministically by monkeypatching
``run_cmd`` (only for the pip_audit invocation -- every other subprocess
call ``main()`` makes, e.g. ``git ls-files``, falls through to the real
``run_cmd`` unchanged) or by calling the pure classification function
directly with synthetic subprocess results.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.quality import bys360_score100_quality_gate_v1 as score100_gate

pytestmark = pytest.mark.ci_safe


# --- classify_dependency_audit_result: pure function, no I/O beyond a temp JSON file ---


def test_classify_returns_pass_on_clean_scan(tmp_path: Path) -> None:
    audit_json = tmp_path / "audit.json"
    audit_json.write_text(json.dumps({"dependencies": [{"name": "flask", "version": "3.0.3", "vulns": []}]}), encoding="utf-8")

    status, reason, packages, vulns = score100_gate.classify_dependency_audit_result(
        return_code=0, stdout="", stderr="", audit_json_path=audit_json, duration_seconds=1.2
    )

    assert status == "PASS"
    assert reason == "clean_scan"
    assert packages == 1
    assert vulns == 0


def test_classify_returns_fail_when_vulnerabilities_found(tmp_path: Path) -> None:
    audit_json = tmp_path / "audit.json"
    audit_json.write_text(
        json.dumps({"dependencies": [{"name": "flask", "version": "3.0.3", "vulns": [{"id": "CVE-FAKE-1"}]}]}),
        encoding="utf-8",
    )

    status, reason, packages, vulns = score100_gate.classify_dependency_audit_result(
        return_code=1, stdout="", stderr="", audit_json_path=audit_json, duration_seconds=3.4
    )

    assert status == "FAIL"
    assert reason == "vulnerabilities_found"
    assert packages == 1
    assert vulns == 1


def test_classify_returns_blocked_on_timeout(tmp_path: Path) -> None:
    audit_json = tmp_path / "audit.json"  # never created -- process never finished

    status, reason, packages, vulns = score100_gate.classify_dependency_audit_result(
        return_code=124, stdout="", stderr="Timeout after 240s", audit_json_path=audit_json, duration_seconds=240.0
    )

    assert status == "BLOCKED"
    assert reason == "timeout"
    assert packages is None
    assert vulns is None


@pytest.mark.parametrize(
    "stderr_text",
    [
        "requests.exceptions.ConnectionError: HTTPSConnectionPool(host='pypi.org', port=443)",
        "socket.gaierror: [Errno 11001] getaddrinfo failed",
        "urllib3.exceptions.NewConnectionError: Failed to establish a new connection",
        "requests.exceptions.SSLError: certificate verify failed",
        "Max retries exceeded with url: /pypi/flask/json",
    ],
)
def test_classify_returns_blocked_on_network_error_markers(tmp_path: Path, stderr_text: str) -> None:
    audit_json = tmp_path / "audit.json"

    status, reason, _packages, _vulns = score100_gate.classify_dependency_audit_result(
        return_code=1, stdout="", stderr=stderr_text, audit_json_path=audit_json, duration_seconds=12.0
    )

    assert status == "BLOCKED"
    assert reason == "network_unreachable"


def test_classify_returns_blocked_when_tool_not_installed(tmp_path: Path) -> None:
    audit_json = tmp_path / "audit.json"

    status, reason, _packages, _vulns = score100_gate.classify_dependency_audit_result(
        return_code=1,
        stdout="",
        stderr="ModuleNotFoundError: No module named 'pip_audit'",
        audit_json_path=audit_json,
        duration_seconds=0.2,
    )

    assert status == "BLOCKED"
    assert reason == "tool_not_available"


def test_classify_returns_fail_undetermined_for_unexplained_nonzero_exit(tmp_path: Path) -> None:
    audit_json = tmp_path / "audit.json"  # not created, no network markers either

    status, reason, packages, vulns = score100_gate.classify_dependency_audit_result(
        return_code=2, stdout="", stderr="unexpected internal pip-audit error", audit_json_path=audit_json, duration_seconds=1.0
    )

    assert status == "FAIL"
    assert reason == "audit_error_undetermined"
    assert packages is None
    assert vulns is None


def test_classify_status_is_always_one_of_the_three_contractual_states(tmp_path: Path) -> None:
    audit_json = tmp_path / "audit.json"
    scenarios = [
        (0, "", ""),
        (1, "", "ModuleNotFoundError: No module named 'pip_audit'"),
        (1, "", "some other real failure"),
        (124, "", "Timeout after 240s"),
        (127, "", ""),
        (1, "", "getaddrinfo failed"),
    ]
    for rc, stdout, stderr in scenarios:
        status, _reason, _packages, _vulns = score100_gate.classify_dependency_audit_result(
            return_code=rc, stdout=stdout, stderr=stderr, audit_json_path=audit_json, duration_seconds=1.0
        )
        assert status in {"PASS", "FAIL", "BLOCKED"}


# --- resolve_dependency_audit_policy ---


def test_policy_explicit_strict_wins_regardless_of_ci_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CI", raising=False)
    assert score100_gate.resolve_dependency_audit_policy("strict") == "strict"


def test_policy_explicit_diagnostic_wins_even_when_ci_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "true")
    assert score100_gate.resolve_dependency_audit_policy("diagnostic") == "diagnostic"


def test_policy_defaults_to_strict_when_ci_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "true")
    assert score100_gate.resolve_dependency_audit_policy(None) == "strict"


def test_policy_defaults_to_diagnostic_when_ci_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CI", raising=False)
    assert score100_gate.resolve_dependency_audit_policy(None) == "diagnostic"


def test_policy_defaults_to_diagnostic_when_ci_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "false")
    assert score100_gate.resolve_dependency_audit_policy(None) == "diagnostic"


# --- main(): Strict/Diagnostic gate-enforcement, no real pip-audit subprocess ---


def _minimal_project(tmp_path: Path) -> Path:
    """A fake project root just complete enough to keep the *other*,
    unrelated Score100 checks green, so these tests isolate the
    dependency-audit policy/status behaviour rather than tripping on
    unrelated findings (e.g. a real BYS360 report-flagged pin version, or
    the duplicate-endpoint-test presence check)."""
    root = tmp_path / "fake_project"
    root.mkdir()
    # Deliberately NOT a report-flagged pin (see KNOWN_REPORT_FLAGGED_PINS).
    (root / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")
    quality_tests_dir = root / "tests" / "quality"
    quality_tests_dir.mkdir(parents=True)
    (quality_tests_dir / "test_app_factory_registers_routes_without_duplicate_endpoints.py").write_text(
        "def test_app_factory_registers_routes_without_duplicate_endpoints():\n    assert True\n",
        encoding="utf-8",
    )
    return root


def _patch_pip_audit_run_cmd(monkeypatch: pytest.MonkeyPatch, *, rc: int, stdout: str = "", stderr: str = "") -> None:
    real_run_cmd = score100_gate.run_cmd

    def _fake_run_cmd(
        cmd: list[str], cwd: Path, timeout: int = 120, env: dict[str, str] | None = None
    ) -> tuple[int, str, str]:
        if len(cmd) >= 3 and cmd[1] == "-m" and cmd[2] == "pip_audit":
            return rc, stdout, stderr
        return real_run_cmd(cmd, cwd, timeout=timeout, env=env)

    monkeypatch.setattr(score100_gate, "run_cmd", _fake_run_cmd)


def test_main_strict_policy_with_blocked_audit_fails_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _minimal_project(tmp_path)
    _patch_pip_audit_run_cmd(monkeypatch, rc=124, stderr="Timeout after 240s")
    output_dir = tmp_path / "out_strict_blocked"

    exit_code = score100_gate.main(
        [
            "--project-root", str(root),
            "--mode", "gate",
            "--output-dir", str(output_dir),
            "--run-pip-audit",
            "--dependency-audit-policy", "strict",
        ]
    )

    assert exit_code == 1
    report = json.loads((output_dir / "BYS360_SCORE100_QUALITY_GATE_V1_REPORT.json").read_text(encoding="utf-8"))
    assert report["dependency_audit"]["dependency_audit_status"] == "BLOCKED"
    assert report["dependency_audit"]["dependency_audit_reason"] == "timeout"


def test_main_diagnostic_policy_with_blocked_audit_does_not_fail_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _minimal_project(tmp_path)
    _patch_pip_audit_run_cmd(monkeypatch, rc=124, stderr="Timeout after 240s")
    output_dir = tmp_path / "out_diagnostic_blocked"

    exit_code = score100_gate.main(
        [
            "--project-root", str(root),
            "--mode", "gate",
            "--output-dir", str(output_dir),
            "--run-pip-audit",
            "--dependency-audit-policy", "diagnostic",
        ]
    )

    # BLOCKED must never be silently reported as a real PASS -- but in
    # Diagnostic policy it also must not hard-fail the whole local gate run.
    assert exit_code == 0
    report = json.loads((output_dir / "BYS360_SCORE100_QUALITY_GATE_V1_REPORT.json").read_text(encoding="utf-8"))
    assert report["dependency_audit"]["dependency_audit_status"] == "BLOCKED"
    assert report["status"] != "FAIL"


def test_main_strict_policy_with_real_vulnerability_fails_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _minimal_project(tmp_path)
    output_dir = tmp_path / "out_strict_vuln"
    output_dir.mkdir(parents=True)
    audit_json = output_dir / "score100_pip_audit_v1.json"
    audit_json.write_text(
        json.dumps({"dependencies": [{"name": "flask", "version": "3.0.3", "vulns": [{"id": "CVE-FAKE-2"}]}]}),
        encoding="utf-8",
    )
    _patch_pip_audit_run_cmd(monkeypatch, rc=1, stderr="")

    exit_code = score100_gate.main(
        [
            "--project-root", str(root),
            "--mode", "gate",
            "--output-dir", str(output_dir),
            "--run-pip-audit",
            "--dependency-audit-policy", "strict",
        ]
    )

    assert exit_code == 1
    report = json.loads((output_dir / "BYS360_SCORE100_QUALITY_GATE_V1_REPORT.json").read_text(encoding="utf-8"))
    assert report["dependency_audit"]["dependency_audit_status"] == "FAIL"


def test_main_diagnostic_policy_with_real_vulnerability_still_fails_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """FAIL is not softened by Diagnostic policy -- only BLOCKED is."""
    root = _minimal_project(tmp_path)
    output_dir = tmp_path / "out_diagnostic_vuln"
    output_dir.mkdir(parents=True)
    audit_json = output_dir / "score100_pip_audit_v1.json"
    audit_json.write_text(
        json.dumps({"dependencies": [{"name": "flask", "version": "3.0.3", "vulns": [{"id": "CVE-FAKE-3"}]}]}),
        encoding="utf-8",
    )
    _patch_pip_audit_run_cmd(monkeypatch, rc=1, stderr="")

    exit_code = score100_gate.main(
        [
            "--project-root", str(root),
            "--mode", "gate",
            "--output-dir", str(output_dir),
            "--run-pip-audit",
            "--dependency-audit-policy", "diagnostic",
        ]
    )

    assert exit_code == 1
    report = json.loads((output_dir / "BYS360_SCORE100_QUALITY_GATE_V1_REPORT.json").read_text(encoding="utf-8"))
    assert report["dependency_audit"]["dependency_audit_status"] == "FAIL"


def test_main_strict_policy_with_real_pass_does_not_fail_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _minimal_project(tmp_path)
    _patch_pip_audit_run_cmd(monkeypatch, rc=0, stdout="", stderr="")
    output_dir = tmp_path / "out_strict_pass"

    exit_code = score100_gate.main(
        [
            "--project-root", str(root),
            "--mode", "gate",
            "--output-dir", str(output_dir),
            "--run-pip-audit",
            "--dependency-audit-policy", "strict",
        ]
    )

    assert exit_code == 0
    report = json.loads((output_dir / "BYS360_SCORE100_QUALITY_GATE_V1_REPORT.json").read_text(encoding="utf-8"))
    assert report["dependency_audit"]["dependency_audit_status"] == "PASS"


def test_main_without_run_pip_audit_flag_reports_no_dependency_audit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _minimal_project(tmp_path)
    output_dir = tmp_path / "out_no_audit"

    exit_code = score100_gate.main(
        [
            "--project-root", str(root),
            "--mode", "audit",
            "--output-dir", str(output_dir),
        ]
    )

    assert exit_code == 0
    report = json.loads((output_dir / "BYS360_SCORE100_QUALITY_GATE_V1_REPORT.json").read_text(encoding="utf-8"))
    assert report["dependency_audit"] == {}
