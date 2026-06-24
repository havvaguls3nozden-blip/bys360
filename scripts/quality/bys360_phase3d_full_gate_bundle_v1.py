from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.quality.bys360_phase3d_import_route_smoke_v1 import run_checks as import_route_smoke_gate
from scripts.quality.bys360_phase3c_score_route_service_gate_v1 import run_checks as score_gate
from scripts.quality.bys360_phase3c_note_route_service_gate_v1 import run_checks as note_gate
from scripts.quality.bys360_phase3c_task_detail_route_service_gate_v1 import run_checks as task_detail_gate
from scripts.quality.bys360_phase3c_summary_risk_route_service_gate_v1 import run_checks as summary_risk_gate
from scripts.quality.bys360_phase3c_compact_route_service_gate_v1 import run_checks as compact_gate


PACKAGE = "BYS360_PHASE3D_FULL_GATE_BUNDLE_V1"
REPORT_REL = Path("reports/architecture/BYS360_PHASE3D_FULL_GATE_BUNDLE_V1_REPORT.json")
SCRIPT_REL = Path("scripts/quality/bys360_phase3d_full_gate_bundle_v1.py")


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).strip()


def _clean_status_ignoring_generated_files(root: Path) -> dict[str, Any]:
    raw = _git(root, "status", "--short").splitlines()
    ignored_paths = {
        str(REPORT_REL).replace("\", "/").lower(),
        str(SCRIPT_REL).replace("\", "/").lower(),
    }

    meaningful = []
    ignored = []

    for line in raw:
        raw_path = line[3:].strip().strip('"').replace("\", "/")
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ")[-1].strip().strip('"').replace("\", "/")

        normalized = raw_path.lower()

        should_ignore = (
            normalized in ignored_paths
            or normalized.endswith(str(REPORT_REL).replace("\", "/").lower())
            or normalized.endswith(str(SCRIPT_REL).replace("\", "/").lower())
        )

        if should_ignore:
            ignored.append(line)
        else:
            meaningful.append(line)

    return {
        "raw": raw,
        "meaningful": meaningful,
        "ignored": ignored,
        "clean": meaningful == [],
    }


def _parse_pytest_summary(output: str) -> dict[str, Any]:
    # Handles:
    # "13 passed, 800 skipped in 5.74s"
    # "1 failed, 12 passed, 800 skipped in 10.20s"
    summary_line = None
    for line in reversed(output.splitlines()):
        if " passed" in line or " skipped" in line or " failed" in line or " error" in line:
            if " in " in line and "=" in line:
                summary_line = line
                break

    if summary_line is None:
        summary_line = ""

    body_match = re.search(r"=+\s*(.*?)\s+in\s+([0-9.]+)s\s*=+", summary_line)
    body = body_match.group(1) if body_match else ""
    seconds = float(body_match.group(2)) if body_match else None

    def _count(name: str) -> int:
        m = re.search(rf"(\d+)\s+{name}", body)
        return int(m.group(1)) if m else 0

    collected_match = re.search(r"collected\s+(\d+)\s+items", output)
    collected = int(collected_match.group(1)) if collected_match else None

    return {
        "collected": collected,
        "passed": _count("passed"),
        "skipped": _count("skipped"),
        "failed": _count("failed"),
        "errors": _count("errors?"),
        "seconds": seconds,
        "summary_found": body_match is not None,
        "summary_line": summary_line,
    }


def run_checks(root: Path, write_report: bool = True) -> dict[str, Any]:
    branch = _git(root, "branch", "--show-current")
    head = _git(root, "rev-parse", "--short", "HEAD")
    status_info = _clean_status_ignoring_generated_files(root)

    gates = {
        "phase3d_import_route_smoke": import_route_smoke_gate(root, write_report=False),
        "phase3c_score_route_service": score_gate(root, write_report=False),
        "phase3c_note_route_service": note_gate(root, write_report=False),
        "phase3c_task_detail_route_service": task_detail_gate(root, write_report=False),
        "phase3c_summary_risk_route_service": summary_risk_gate(root, write_report=False),
        "phase3c_compact_route_service": compact_gate(root, write_report=False),
    }

    pytest_cmd = [sys.executable, "-m", "pytest"]
    pytest_run = subprocess.run(
        pytest_cmd,
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )

    pytest_output = (pytest_run.stdout or "") + "\n" + (pytest_run.stderr or "")
    pytest_summary = _parse_pytest_summary(pytest_output)

    gate_expectations = {
        "phase3d_import_route_smoke": gates["phase3d_import_route_smoke"].get("phase3d_import_route_smoke_ok") is True,
        "phase3c_score_route_service": gates["phase3c_score_route_service"].get("score_route_service_gate_ok") is True,
        "phase3c_note_route_service": gates["phase3c_note_route_service"].get("note_route_service_gate_ok") is True,
        "phase3c_task_detail_route_service": gates["phase3c_task_detail_route_service"].get("task_detail_route_service_gate_ok") is True,
        "phase3c_summary_risk_route_service": gates["phase3c_summary_risk_route_service"].get("summary_risk_route_service_gate_ok") is True,
        "phase3c_compact_route_service": gates["phase3c_compact_route_service"].get("compact_route_service_gate_ok") is True,
    }

    result: dict[str, Any] = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "branch": branch,
        "head_before_report_commit": head,
        "git_status_before_bundle": status_info,
        "meaningful_git_status_clean_before_bundle": status_info["clean"],
        "gates": gates,
        "gate_expectations": gate_expectations,
        "all_gates_ok": all(gate_expectations.values()),
        "pytest": {
            "command": " ".join(pytest_cmd),
            "returncode": pytest_run.returncode,
            "summary": pytest_summary,
            "stdout_tail": (pytest_run.stdout or "")[-6000:],
            "stderr_tail": (pytest_run.stderr or "")[-2000:],
        },
        "pytest_ok": (
            pytest_run.returncode == 0
            and pytest_summary.get("passed") == 13
            and pytest_summary.get("skipped") == 800
            and pytest_summary.get("failed") == 0
            and pytest_summary.get("errors") == 0
        ),
        "phase3d_full_gate_bundle_ok": False,
    }

    result["phase3d_full_gate_bundle_ok"] = bool(
        result["meaningful_git_status_clean_before_bundle"]
        and result["all_gates_ok"]
        and result["pytest_ok"]
        and gates["phase3d_import_route_smoke"].get("route_decorator_count") == 22
        and gates["phase3d_import_route_smoke"].get("route_lines") == 1164
    )

    if write_report:
        report = root / REPORT_REL
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        result["report"] = str(report)

    return result


def main() -> int:
    root = Path.cwd()
    result = run_checks(root, write_report=True)

    print(json.dumps({
        "phase3d_full_gate_bundle_ok": result["phase3d_full_gate_bundle_ok"],
        "branch": result["branch"],
        "head_before_report_commit": result["head_before_report_commit"],
        "meaningful_git_status_clean_before_bundle": result["meaningful_git_status_clean_before_bundle"],
        "ignored_status_lines": result["git_status_before_bundle"]["ignored"],
        "all_gates_ok": result["all_gates_ok"],
        "pytest_ok": result["pytest_ok"],
        "pytest_summary": result["pytest"]["summary"],
        "route_lines": result["gates"]["phase3d_import_route_smoke"].get("route_lines"),
        "route_decorator_count": result["gates"]["phase3d_import_route_smoke"].get("route_decorator_count"),
        "report": result.get("report"),
    }, ensure_ascii=False, indent=2))

    return 0 if result["phase3d_full_gate_bundle_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
