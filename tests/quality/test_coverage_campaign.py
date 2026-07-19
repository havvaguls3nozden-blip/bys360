from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MODULE_PATH = (
    ROOT
    / "scripts"
    / "quality"
    / "bys360_coverage_campaign.py"
)

SPEC = importlib.util.spec_from_file_location(
    "bys360_coverage_campaign",
    MODULE_PATH,
)

assert SPEC is not None
assert SPEC.loader is not None

campaign = importlib.util.module_from_spec(
    SPEC
)

SPEC.loader.exec_module(campaign)


def _file_record(
    *,
    statements=10,
    covered_lines=5,
    branches=4,
    covered_branches=1,
):
    missing_lines = (
        statements - covered_lines
    )

    missing_branches = (
        branches - covered_branches
    )

    return {
        "summary": {
            "num_statements": statements,
            "covered_lines": covered_lines,
            "missing_lines": missing_lines,
            "num_branches": branches,
            "covered_branches": (
                covered_branches
            ),
            "missing_branches": (
                missing_branches
            ),
            "percent_covered": (
                (
                    covered_lines
                    + covered_branches
                )
                / (
                    statements
                    + branches
                )
                * 100.0
            ),
        },
        "missing_lines": list(
            range(
                covered_lines + 1,
                statements + 1,
            )
        ),
        "missing_branches": [
            [index, index + 1]
            for index in range(
                covered_branches + 1,
                branches + 1,
            )
        ],
    }


def _coverage(
    *,
    covered_lines=5,
    covered_branches=1,
    statements=10,
    branches=4,
):
    record = _file_record(
        statements=statements,
        covered_lines=covered_lines,
        branches=branches,
        covered_branches=(
            covered_branches
        ),
    )

    return {
        "totals": dict(
            record["summary"]
        ),
        "files": {
            "app/services/settings/"
            "sample.py": record,
        },
    }


def test_summarize_coverage_calculates_metrics():
    result = campaign.summarize_coverage(
        _coverage()
    )

    assert result["num_statements"] == 10
    assert result["covered_lines"] == 5
    assert result["num_branches"] == 4
    assert result["covered_branches"] == 1

    assert result[
        "statement_percent"
    ] == 50.0

    assert result[
        "branch_percent"
    ] == 25.0


def test_campaign_accepts_improvement():
    before = _coverage(
        covered_lines=5,
        covered_branches=1,
    )

    after = _coverage(
        covered_lines=8,
        covered_branches=3,
    )

    report = campaign.build_campaign_report(
        before=before,
        after=after,
        targets=[
            "app/services/settings/"
            "sample.py"
        ],
        gate_baseline={
            "min_total_percent": 0.0,
            "min_branch_percent": 0.0,
        },
        require_same_denominators=True,
        require_target_improvement=True,
    )

    assert report["ok"] is True
    assert report["errors"] == []

    assert (
        report["deltas"][
            "covered_lines"
        ]
        == 3
    )

    assert (
        report["targets"][0][
            "improved"
        ]
        is True
    )


def test_campaign_rejects_regression():
    before = _coverage(
        covered_lines=8,
        covered_branches=3,
    )

    after = _coverage(
        covered_lines=7,
        covered_branches=2,
    )

    report = campaign.build_campaign_report(
        before=before,
        after=after,
        targets=[],
        gate_baseline={
            "min_total_percent": 0.0,
            "min_branch_percent": 0.0,
        },
    )

    assert report["ok"] is False

    assert any(
        "regressed" in error
        for error in report["errors"]
    )


def test_campaign_checks_denominators():
    before = _coverage(
        statements=10,
    )

    after = _coverage(
        statements=11,
    )

    report = campaign.build_campaign_report(
        before=before,
        after=after,
        targets=[],
        gate_baseline={
            "min_total_percent": 0.0,
            "min_branch_percent": 0.0,
        },
        require_same_denominators=True,
    )

    assert report["ok"] is False

    assert (
        "coverage denominators changed"
        in report["errors"]
    )


def test_campaign_can_require_full_target():
    before = _coverage(
        covered_lines=5,
        covered_branches=1,
    )

    after = _coverage(
        covered_lines=9,
        covered_branches=4,
    )

    report = campaign.build_campaign_report(
        before=before,
        after=after,
        targets=[
            "app/services/settings/"
            "sample.py"
        ],
        gate_baseline={
            "min_total_percent": 0.0,
            "min_branch_percent": 0.0,
        },
        require_target_full=True,
    )

    assert report["ok"] is False

    assert any(
        "target is not full" in error
        for error in report["errors"]
    )


def test_read_gate_baseline(tmp_path):
    gate_path = tmp_path / "gate.py"

    gate_path.write_text(
        "\n".join(
            [
                "DEFAULT_MIN_TOTAL = 21.13",
                "DEFAULT_MIN_BRANCH = 6.74",
                "",
            ]
        ),
        encoding="utf-8",
    )

    baseline = campaign.read_gate_baseline(
        gate_path
    )

    assert baseline == {
        "min_total_percent": 21.13,
        "min_branch_percent": 6.74,
    }


def test_cli_writes_json_and_markdown(
    tmp_path,
):
    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    gate_path = tmp_path / "gate.py"

    json_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"

    before_path.write_text(
        json.dumps(_coverage()),
        encoding="utf-8",
    )

    after_path.write_text(
        json.dumps(
            _coverage(
                covered_lines=8,
                covered_branches=3,
            )
        ),
        encoding="utf-8",
    )

    gate_path.write_text(
        "\n".join(
            [
                "DEFAULT_MIN_TOTAL = 0.0",
                "DEFAULT_MIN_BRANCH = 0.0",
                "",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = campaign.main(
        [
            "--before",
            str(before_path),
            "--after",
            str(after_path),
            "--target",
            (
                "app/services/settings/"
                "sample.py"
            ),
            "--gate-script",
            str(gate_path),
            "--require-same-denominators",
            "--require-target-improvement",
            "--output-json",
            str(json_path),
            "--output-markdown",
            str(markdown_path),
        ]
    )

    assert exit_code == 0
    assert json_path.exists()
    assert markdown_path.exists()

    report = json.loads(
        json_path.read_text(
            encoding="utf-8",
        )
    )

    assert report["ok"] is True
    assert "PASS" in markdown_path.read_text(
        encoding="utf-8",
    )
