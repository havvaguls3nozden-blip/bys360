"""Reusable BYS360 coverage campaign comparison tool."""

from __future__ import annotations

import argparse
import json
import re
from decimal import ROUND_DOWN, Decimal
from pathlib import Path
from typing import Any

EPSILON = 1e-12

DEFAULT_GATE_SCRIPT = Path(
    "scripts/quality/"
    "bys360_coverage_regression_gate_phase4n.py"
)


def normalize_path(value: str) -> str:
    return value.replace("\\", "/")


def percent(
    numerator: int,
    denominator: int,
) -> float:
    if denominator <= 0:
        return 100.0

    return (
        numerator
        / denominator
        * 100.0
    )


def floor_two(value: float) -> str:
    return format(
        Decimal(str(value)).quantize(
            Decimal("0.01"),
            rounding=ROUND_DOWN,
        ),
        ".2f",
    )


def load_coverage(
    path: Path,
) -> dict[str, Any]:
    payload = json.loads(
        path.read_text(
            encoding="utf-8-sig",
        )
    )

    if not isinstance(
        payload.get("totals"),
        dict,
    ):
        raise ValueError(
            f"Coverage totals missing: {path}"
        )

    if not isinstance(
        payload.get("files"),
        dict,
    ):
        raise ValueError(
            f"Coverage files missing: {path}"
        )

    return payload


def summarize_coverage(
    payload: dict[str, Any],
) -> dict[str, Any]:
    totals = payload.get("totals") or {}
    files = payload.get("files") or {}

    statements = int(
        totals.get("num_statements")
        or 0
    )

    covered_lines = int(
        totals.get("covered_lines")
        or 0
    )

    missing_lines = int(
        totals.get("missing_lines")
        or 0
    )

    branches = int(
        totals.get("num_branches")
        or 0
    )

    covered_branches = int(
        totals.get("covered_branches")
        or 0
    )

    missing_branches = int(
        totals.get("missing_branches")
        or 0
    )

    combined = totals.get(
        "percent_covered"
    )

    if combined is None:
        combined = percent(
            covered_lines
            + covered_branches,
            statements
            + branches,
        )

    return {
        "total_percent": float(combined),
        "statement_percent": percent(
            covered_lines,
            statements,
        ),
        "branch_percent": percent(
            covered_branches,
            branches,
        ),
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
        "measured_file_count": len(files),
    }


def find_file_payload(
    coverage: dict[str, Any],
    target: str,
) -> dict[str, Any]:
    normalized_target = normalize_path(
        target
    ).lstrip("./")

    matches = [
        payload
        for name, payload
        in (
            coverage.get("files")
            or {}
        ).items()
        if normalize_path(name).endswith(
            normalized_target
        )
    ]

    if len(matches) != 1:
        raise ValueError(
            "Coverage target record count "
            f"for {target}: {len(matches)}"
        )

    return matches[0]


def summarize_target(
    coverage: dict[str, Any],
    target: str,
) -> dict[str, Any]:
    payload = find_file_payload(
        coverage,
        target,
    )

    summary = payload.get("summary") or {}

    return {
        "path": normalize_path(target),
        "num_statements": int(
            summary.get("num_statements")
            or 0
        ),
        "covered_lines": int(
            summary.get("covered_lines")
            or 0
        ),
        "missing_lines": int(
            summary.get("missing_lines")
            or 0
        ),
        "num_branches": int(
            summary.get("num_branches")
            or 0
        ),
        "covered_branches": int(
            summary.get("covered_branches")
            or 0
        ),
        "missing_branches": int(
            summary.get("missing_branches")
            or 0
        ),
        "percent_covered": float(
            summary.get("percent_covered")
            or 0.0
        ),
        "missing_line_numbers": sorted(
            int(value)
            for value in (
                payload.get("missing_lines")
                or []
            )
        ),
        "missing_branch_arcs": sorted(
            [
                [
                    int(item[0]),
                    int(item[1]),
                ]
                for item in (
                    payload.get(
                        "missing_branches"
                    )
                    or []
                )
                if (
                    isinstance(item, list)
                    and len(item) == 2
                )
            ]
        ),
    }


def read_gate_baseline(
    path: Path,
) -> dict[str, float]:
    source = path.read_text(
        encoding="utf-8-sig",
        errors="strict",
    )

    def read_constant(
        name: str,
    ) -> float:
        match = re.search(
            rf"^{re.escape(name)}\s*=\s*"
            r"([-+]?[0-9]+(?:\.[0-9]+)?)"
            r"\s*$",
            source,
            flags=re.MULTILINE,
        )

        if match is None:
            raise ValueError(
                f"Gate constant missing: {name}"
            )

        return float(match.group(1))

    return {
        "min_total_percent": read_constant(
            "DEFAULT_MIN_TOTAL"
        ),
        "min_branch_percent": read_constant(
            "DEFAULT_MIN_BRANCH"
        ),
    }


def build_campaign_report(
    *,
    before: dict[str, Any],
    after: dict[str, Any],
    targets: list[str],
    gate_baseline: dict[str, float],
    require_same_denominators: bool = False,
    require_target_improvement: bool = False,
    require_target_full: bool = False,
) -> dict[str, Any]:
    before_summary = summarize_coverage(
        before
    )

    after_summary = summarize_coverage(
        after
    )

    denominator_same = (
        before_summary["num_statements"]
        == after_summary["num_statements"]
        and before_summary["num_branches"]
        == after_summary["num_branches"]
        and before_summary[
            "measured_file_count"
        ]
        == after_summary[
            "measured_file_count"
        ]
    )

    deltas = {
        key: (
            after_summary[key]
            - before_summary[key]
        )
        for key in (
            "total_percent",
            "statement_percent",
            "branch_percent",
            "num_statements",
            "covered_lines",
            "missing_lines",
            "num_branches",
            "covered_branches",
            "missing_branches",
            "measured_file_count",
        )
    }

    errors: list[str] = []

    for metric in (
        "total_percent",
        "statement_percent",
        "branch_percent",
    ):
        if (
            after_summary[metric]
            + EPSILON
            < before_summary[metric]
        ):
            errors.append(
                f"{metric} regressed"
            )

    if (
        require_same_denominators
        and not denominator_same
    ):
        errors.append(
            "coverage denominators changed"
        )

    gate_checks = {
        "total_ok": (
            after_summary["total_percent"]
            + EPSILON
            >= gate_baseline[
                "min_total_percent"
            ]
        ),
        "branch_ok": (
            after_summary["branch_percent"]
            + EPSILON
            >= gate_baseline[
                "min_branch_percent"
            ]
        ),
    }

    if not gate_checks["total_ok"]:
        errors.append(
            "total coverage is below gate"
        )

    if not gate_checks["branch_ok"]:
        errors.append(
            "branch coverage is below gate"
        )

    target_records: list[
        dict[str, Any]
    ] = []

    for target in targets:
        before_target = summarize_target(
            before,
            target,
        )

        after_target = summarize_target(
            after,
            target,
        )

        improved = (
            after_target["covered_lines"]
            > before_target["covered_lines"]
            or after_target[
                "covered_branches"
            ]
            > before_target[
                "covered_branches"
            ]
            or after_target[
                "percent_covered"
            ]
            > before_target[
                "percent_covered"
            ]
            + EPSILON
        )

        full = (
            after_target["missing_lines"]
            == 0
            and after_target[
                "missing_branches"
            ]
            == 0
        )

        target_record = {
            "path": normalize_path(
                target
            ),
            "before": before_target,
            "after": after_target,
            "delta": {
                "covered_lines": (
                    after_target[
                        "covered_lines"
                    ]
                    - before_target[
                        "covered_lines"
                    ]
                ),
                "missing_lines": (
                    after_target[
                        "missing_lines"
                    ]
                    - before_target[
                        "missing_lines"
                    ]
                ),
                "covered_branches": (
                    after_target[
                        "covered_branches"
                    ]
                    - before_target[
                        "covered_branches"
                    ]
                ),
                "missing_branches": (
                    after_target[
                        "missing_branches"
                    ]
                    - before_target[
                        "missing_branches"
                    ]
                ),
                "percent_covered": (
                    after_target[
                        "percent_covered"
                    ]
                    - before_target[
                        "percent_covered"
                    ]
                ),
            },
            "improved": improved,
            "full_coverage": full,
        }

        if (
            require_target_improvement
            and not improved
        ):
            errors.append(
                f"target did not improve: "
                f"{target}"
            )

        if (
            require_target_full
            and not full
        ):
            errors.append(
                f"target is not full: "
                f"{target}"
            )

        target_records.append(
            target_record
        )

    return {
        "ok": not errors,
        "before": before_summary,
        "after": after_summary,
        "deltas": deltas,
        "denominators_unchanged": (
            denominator_same
        ),
        "gate": {
            "baseline": gate_baseline,
            "checks": gate_checks,
        },
        "suggested_baseline": {
            "total": floor_two(
                after_summary[
                    "total_percent"
                ]
            ),
            "branch": floor_two(
                after_summary[
                    "branch_percent"
                ]
            ),
        },
        "targets": target_records,
        "requirements": {
            "same_denominators": (
                require_same_denominators
            ),
            "target_improvement": (
                require_target_improvement
            ),
            "target_full": (
                require_target_full
            ),
        },
        "errors": errors,
    }


def render_markdown(
    report: dict[str, Any],
) -> str:
    before = report["before"]
    after = report["after"]
    deltas = report["deltas"]

    lines = [
        "# BYS360 Coverage Campaign Report",
        "",
        (
            f"- Result: "
            f"{'PASS' if report['ok'] else 'FAIL'}"
        ),
        (
            "- Total coverage: "
            f"{before['total_percent']:.6f} -> "
            f"{after['total_percent']:.6f}"
        ),
        (
            "- Statement coverage: "
            f"{before['statement_percent']:.6f} -> "
            f"{after['statement_percent']:.6f}"
        ),
        (
            "- Branch coverage: "
            f"{before['branch_percent']:.6f} -> "
            f"{after['branch_percent']:.6f}"
        ),
        (
            "- Covered lines delta: "
            f"{deltas['covered_lines']:+d}"
        ),
        (
            "- Covered branches delta: "
            f"{deltas['covered_branches']:+d}"
        ),
        (
            "- Suggested baseline: "
            f"{report['suggested_baseline']['total']} "
            f"total / "
            f"{report['suggested_baseline']['branch']} "
            f"branch"
        ),
        "",
        "## Targets",
        "",
    ]

    if not report["targets"]:
        lines.append(
            "- No target files supplied."
        )

    for target in report["targets"]:
        lines.append(
            "- "
            + target["path"]
            + ": "
            + (
                "full"
                if target["full_coverage"]
                else "partial"
            )
            + ", delta lines "
            + f"{target['delta']['covered_lines']:+d}"
            + ", delta branches "
            + f"{target['delta']['covered_branches']:+d}"
        )

    if report["errors"]:
        lines.extend(
            [
                "",
                "## Errors",
                "",
            ]
        )

        for error in report["errors"]:
            lines.append(
                f"- {error}"
            )

    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare two coverage.py JSON "
            "reports for a BYS360 campaign."
        )
    )

    parser.add_argument(
        "--before",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--after",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--target",
        action="append",
        default=[],
    )

    parser.add_argument(
        "--gate-script",
        type=Path,
        default=DEFAULT_GATE_SCRIPT,
    )

    parser.add_argument(
        "--require-same-denominators",
        action="store_true",
    )

    parser.add_argument(
        "--require-target-improvement",
        action="store_true",
    )

    parser.add_argument(
        "--require-target-100",
        action="store_true",
    )

    parser.add_argument(
        "--output-json",
        type=Path,
    )

    parser.add_argument(
        "--output-markdown",
        type=Path,
    )

    return parser


def main(
    argv: list[str] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    before = load_coverage(
        args.before
    )

    after = load_coverage(
        args.after
    )

    gate_baseline = read_gate_baseline(
        args.gate_script
    )

    report = build_campaign_report(
        before=before,
        after=after,
        targets=list(args.target),
        gate_baseline=gate_baseline,
        require_same_denominators=(
            args.require_same_denominators
        ),
        require_target_improvement=(
            args.require_target_improvement
        ),
        require_target_full=(
            args.require_target_100
        ),
    )

    rendered_json = json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
    )

    print(rendered_json)

    if args.output_json:
        args.output_json.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        args.output_json.write_text(
            rendered_json + "\n",
            encoding="utf-8",
            newline="\n",
        )

    if args.output_markdown:
        args.output_markdown.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        args.output_markdown.write_text(
            render_markdown(report),
            encoding="utf-8",
            newline="\n",
        )

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
