from __future__ import annotations

import json
from pathlib import Path

from scripts.quality.bys360_coverage_regression_gate_phase4n import build_report


def _write_coverage(path: Path, total: float, branch: float) -> None:
    path.write_text(
        json.dumps(
            {
                "totals": {
                    "percent_covered": total,
                    "percent_branches_covered": branch,
                    "covered_lines": 22845,
                    "num_statements": 102900,
                    "missing_lines": 80055,
                    "covered_branches": 1054,
                    "missing_branches": 28594,
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_coverage_regression_gate_accepts_current_baseline(tmp_path: Path) -> None:
    coverage_json = tmp_path / "coverage.json"
    _write_coverage(coverage_json, total=21.09208999532844, branch=6.712291821185355)

    report = build_report(coverage_json)

    assert report["ok"] is True
    assert report["checks"]["total_ok"] is True
    assert report["checks"]["branch_ok"] is True


def test_coverage_regression_gate_rejects_total_regression(tmp_path: Path) -> None:
    coverage_json = tmp_path / "coverage.json"
    _write_coverage(coverage_json, total=21.08, branch=6.712291821185355)

    report = build_report(coverage_json)

    assert report["ok"] is False
    assert report["checks"]["total_ok"] is False


def test_coverage_regression_gate_rejects_branch_regression(tmp_path: Path) -> None:
    coverage_json = tmp_path / "coverage.json"
    _write_coverage(coverage_json, total=21.09208999532844, branch=6.7)

    report = build_report(coverage_json)

    assert report["ok"] is False
    assert report["checks"]["branch_ok"] is False
