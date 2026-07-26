from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.quality import bys360_coverage_ratchet as ratchet

pytestmark = pytest.mark.ci_safe

ROOT = Path(__file__).resolve().parents[2]


def _write_coverage_xml(
    path: Path,
    *,
    lines_valid: int,
    lines_covered: int,
    branches_valid: int = 0,
    branches_covered: int = 0,
) -> None:
    path.write_text(
        (
            '<coverage version="test" '
            f'lines-valid="{lines_valid}" lines-covered="{lines_covered}" '
            f'branches-valid="{branches_valid}" branches-covered="{branches_covered}" />'
        ),
        encoding="utf-8",
    )


def _write_baseline(path: Path, *, combined_pct: float, tolerance_pct: float) -> None:
    path.write_text(
        json.dumps(
            {
                "combined_pct": combined_pct,
                "tolerance_pct": tolerance_pct,
            }
        ),
        encoding="utf-8",
    )


def test_committed_baseline_counts_are_internally_consistent() -> None:
    baseline = json.loads(
        (ROOT / "reports" / "quality" / "coverage_baseline.json").read_text(
            encoding="utf-8"
        )
    )

    combined_pct = (
        (baseline["lines_covered"] + baseline["branches_covered"])
        / (baseline["lines_valid"] + baseline["branches_valid"])
        * 100.0
    )

    assert combined_pct == pytest.approx(baseline["combined_pct_precise"])
    assert round(combined_pct, 2) == baseline["combined_pct"]


def test_coverage_ratchet_accepts_measurement_at_baseline(tmp_path: Path) -> None:
    coverage_xml = tmp_path / "coverage.xml"
    baseline = tmp_path / "coverage_baseline.json"
    _write_coverage_xml(
        coverage_xml,
        lines_valid=100,
        lines_covered=50,
    )
    _write_baseline(
        baseline,
        combined_pct=50.0,
        tolerance_pct=0.5,
    )

    exit_code = ratchet.main(
        [
            "--coverage-xml",
            str(coverage_xml),
            "--baseline",
            str(baseline),
        ]
    )

    assert exit_code == 0


def test_coverage_ratchet_rejects_regression_below_tolerance(
    tmp_path: Path,
) -> None:
    coverage_xml = tmp_path / "coverage.xml"
    baseline = tmp_path / "coverage_baseline.json"
    _write_coverage_xml(
        coverage_xml,
        lines_valid=100,
        lines_covered=49,
    )
    _write_baseline(
        baseline,
        combined_pct=50.0,
        tolerance_pct=0.5,
    )

    exit_code = ratchet.main(
        [
            "--coverage-xml",
            str(coverage_xml),
            "--baseline",
            str(baseline),
        ]
    )

    assert exit_code == 1


def test_coverage_ratchet_rejects_missing_measurement(tmp_path: Path) -> None:
    baseline = tmp_path / "coverage_baseline.json"
    _write_baseline(
        baseline,
        combined_pct=50.0,
        tolerance_pct=0.5,
    )

    exit_code = ratchet.main(
        [
            "--coverage-xml",
            str(tmp_path / "missing.xml"),
            "--baseline",
            str(baseline),
        ]
    )

    assert exit_code == 2
