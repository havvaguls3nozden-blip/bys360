from __future__ import annotations

import json
from pathlib import Path

from scripts.quality.bys360_coverage_regression_gate_phase4n import (
    DEFAULT_MIN_BRANCH,
    DEFAULT_MIN_TOTAL,
    build_report,
)


CURRENT_TOTAL = 21.419099142542837
CURRENT_BRANCH = 7.049423504820982


def _write_coverage(
    path: Path,
    total: float,
    branch: float,
) -> None:
    path.write_text(
        json.dumps(
            {
                "totals": {
                    "percent_covered": total,
                    "percent_branches_covered": branch,
                    "covered_lines": 26336,
                    "num_statements": 103056,
                    "missing_lines": 76720,
                    "covered_branches": 2091,
                    "missing_branches": 27571,
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_coverage_gate_defaults_match_campaign1_baseline():
    assert DEFAULT_MIN_TOTAL == 21.41
    assert DEFAULT_MIN_BRANCH == 7.04


def test_coverage_gate_accepts_campaign1_measurement(
    tmp_path: Path,
):
    coverage_json = tmp_path / "coverage.json"

    _write_coverage(
        coverage_json,
        total=CURRENT_TOTAL,
        branch=CURRENT_BRANCH,
    )

    report = build_report(
        coverage_json
    )

    assert report["ok"] is True
    assert report["checks"]["total_ok"] is True
    assert report["checks"]["branch_ok"] is True
    assert report["baseline"] == {
        "min_total_percent": 21.41,
        "min_branch_percent": 7.04,
    }


def test_coverage_gate_accepts_exact_new_floor(
    tmp_path: Path,
):
    coverage_json = tmp_path / "coverage.json"

    _write_coverage(
        coverage_json,
        total=21.41,
        branch=7.04,
    )

    report = build_report(
        coverage_json
    )

    assert report["ok"] is True
    assert report["checks"]["total_ok"] is True
    assert report["checks"]["branch_ok"] is True


def test_coverage_gate_rejects_total_regression(
    tmp_path: Path,
):
    coverage_json = tmp_path / "coverage.json"

    _write_coverage(
        coverage_json,
        total=21.40,
        branch=CURRENT_BRANCH,
    )

    report = build_report(
        coverage_json
    )

    assert report["ok"] is False
    assert report["checks"]["total_ok"] is False
    assert report["checks"]["branch_ok"] is True


def test_coverage_gate_rejects_branch_regression(
    tmp_path: Path,
):
    coverage_json = tmp_path / "coverage.json"

    _write_coverage(
        coverage_json,
        total=CURRENT_TOTAL,
        branch=7.03,
    )

    report = build_report(
        coverage_json
    )

    assert report["ok"] is False
    assert report["checks"]["total_ok"] is True
    assert report["checks"]["branch_ok"] is False
