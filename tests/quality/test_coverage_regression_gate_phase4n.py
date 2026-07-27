from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.quality.bys360_coverage_regression_gate_phase4n import (
    DEFAULT_MIN_BRANCH,
    DEFAULT_MIN_TOTAL,
    build_report,
)

pytestmark = pytest.mark.ci_safe

CURRENT_TOTAL = 21.852348588737023
CURRENT_BRANCH = 7.716944238419527


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
                    "covered_lines": 26713,
                    "num_statements": 103056,
                    "missing_lines": 76343,
                    "covered_branches": 2289,
                    "missing_branches": 27373,
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_coverage_gate_defaults_match_campaign1_baseline():
    assert DEFAULT_MIN_TOTAL == 21.85
    assert DEFAULT_MIN_BRANCH == 7.71


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
        "min_total_percent": 21.85,
        "min_branch_percent": 7.71,
    }


def test_coverage_gate_accepts_exact_new_floor(
    tmp_path: Path,
):
    coverage_json = tmp_path / "coverage.json"

    _write_coverage(
        coverage_json,
        total=21.85,
        branch=7.71,
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
        total=21.84,
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
        branch=7.70,
    )

    report = build_report(
        coverage_json
    )

    assert report["ok"] is False
    assert report["checks"]["total_ok"] is True
    assert report["checks"]["branch_ok"] is False
