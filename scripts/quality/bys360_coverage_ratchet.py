"""BYS360 coverage ratchet.

Purpose
-------
Compares the combined line+branch coverage percentage in a freshly generated
Cobertura-format ``coverage.xml`` (produced by ``pytest-cov``'s
``--cov-report=xml``) against a stored baseline percentage, and fails loudly
if coverage has genuinely dropped below that baseline.

This exists because ``pyproject.toml``'s ``[tool.coverage.report] fail_under``
is a *static*, easily-forgotten number that pytest-cov enforces per-invocation
(which breaks a two-step "quality tests, then broader tests, with
--cov-append" CI sequence -- the first, partial step would never reach
fail_under on its own). This script instead enforces the floor once, at the
end, against the final combined XML report -- independent of how many pytest
invocations contributed to it.

Why "ratchet"
-------------
A ratchet only tightens. This script will refuse to pass if coverage drops
below the stored baseline (within a small tolerance -- see below), but it
will NEVER rewrite reports/quality/coverage_baseline.json itself, even when
the newly measured coverage is higher than the stored baseline. Raising the
baseline is a deliberate, human-reviewed action: someone must look at *why*
coverage went up (new tests? more of the app now exercised? scope
change?) and decide the new number is a legitimate, durable floor before
committing it. Silently auto-raising the baseline on every green run would
let a temporary/flaky improvement silently become the new required floor,
which is exactly the kind of unearned ratchet this script must not create.
If you want to raise the baseline, edit reports/quality/coverage_baseline.json
by hand (or a separate, explicitly-named tool) and say why in the commit.

Tolerance
---------
A small default tolerance (0.5 percentage points -- see
reports/quality/coverage_baseline.json's "tolerance_pct" field, which this
script reads and uses as its default) is subtracted from the baseline before
comparison. This exists to absorb float rounding and platform noise (e.g.
this baseline was measured on a Windows worktree; BYS360 CI itself runs on
ubuntu-latest, and OS-conditional code paths can shift the covered-line count
by a handful of lines out of 100k+ without any real regression). It is not
meant to, and in practice will not, absorb an actual coverage regression --
those are expected to be much larger than half a percentage point.

Usage
-----
    python scripts/quality/bys360_coverage_ratchet.py \\
        --coverage-xml reports/quality/coverage.xml \\
        --baseline reports/quality/coverage_baseline.json

Exit codes
----------
0   New combined coverage meets or exceeds (baseline - tolerance).
1   New combined coverage is below (baseline - tolerance) -- real regression.
2   Usage / input error (missing file, unparsable XML, malformed baseline).

Stdlib only: xml.etree.ElementTree, json, argparse, sys, pathlib.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

DEFAULT_TOLERANCE_PCT = 0.5


def compute_combined_pct(coverage_xml_path: Path) -> tuple[float, dict[str, float]]:
    """Compute the combined line+branch coverage percentage from a Cobertura XML.

    Mirrors coverage.py's own combined-percentage formula when branch
    coverage is enabled (branch=true): the numerator is covered lines plus
    covered branches, the denominator is valid (measurable) lines plus valid
    branches. This is the same figure pytest-cov prints as "TOTAL ... Cover"
    in its terminal report and the same one fail_under is checked against.

    Returns (combined_pct, details) where details holds the raw counts used,
    for transparent reporting.
    """
    try:
        root = ET.parse(coverage_xml_path).getroot()
    except ET.ParseError as exc:
        raise SystemExit(f"ERROR: could not parse '{coverage_xml_path}' as XML: {exc}") from exc

    def _int_attr(name: str) -> int:
        raw = root.get(name)
        if raw is None:
            raise SystemExit(
                f"ERROR: '{coverage_xml_path}' is missing the '{name}' attribute on "
                "its root <coverage> element -- is this really a pytest-cov / "
                "coverage.py Cobertura XML report?"
            )
        return int(raw)

    lines_valid = _int_attr("lines-valid")
    lines_covered = _int_attr("lines-covered")
    branches_valid = _int_attr("branches-valid")
    branches_covered = _int_attr("branches-covered")

    denominator = lines_valid + branches_valid
    if denominator == 0:
        raise SystemExit(
            f"ERROR: '{coverage_xml_path}' reports zero valid lines and zero valid "
            "branches -- nothing was measured. Refusing to compute a percentage "
            "from a 0/0 division (this would be meaningless, not 0% or 100%)."
        )

    combined_pct = (lines_covered + branches_covered) / denominator * 100.0

    details = {
        "lines_covered": lines_covered,
        "lines_valid": lines_valid,
        "branches_covered": branches_covered,
        "branches_valid": branches_valid,
        "line_pct": (lines_covered / lines_valid * 100.0) if lines_valid else 0.0,
        "branch_pct": (branches_covered / branches_valid * 100.0) if branches_valid else 0.0,
    }
    return combined_pct, details


def load_baseline(baseline_path: Path) -> dict:
    try:
        raw = baseline_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"ERROR: could not read baseline file '{baseline_path}': {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: baseline file '{baseline_path}' is not valid JSON: {exc}") from exc

    if "combined_pct" not in data:
        raise SystemExit(
            f"ERROR: baseline file '{baseline_path}' has no 'combined_pct' key. "
            "This script never invents a baseline -- fix the file."
        )
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fail if coverage.xml's combined line+branch coverage percentage has "
            "dropped below the stored baseline (see reports/quality/coverage_baseline.json). "
            "Never raises the baseline itself -- that is a separate, human-reviewed action."
        )
    )
    parser.add_argument(
        "--coverage-xml",
        type=Path,
        default=Path("reports/quality/coverage.xml"),
        help="Path to the Cobertura-format coverage.xml produced by pytest-cov's "
        "--cov-report=xml (default: reports/quality/coverage.xml)",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("reports/quality/coverage_baseline.json"),
        help="Path to the JSON baseline file (default: reports/quality/coverage_baseline.json)",
    )
    parser.add_argument(
        "--tolerance-pct",
        type=float,
        default=None,
        help="Percentage points of slack subtracted from the baseline before comparison. "
        "Defaults to the baseline file's own 'tolerance_pct' field, or "
        f"{DEFAULT_TOLERANCE_PCT} if that field is absent.",
    )
    args = parser.parse_args(argv)

    if not args.coverage_xml.exists():
        print(
            f"FAIL: coverage XML not found at '{args.coverage_xml}'. "
            "Run the pytest + --cov-report=xml steps before calling this script.",
            file=sys.stderr,
        )
        return 2

    if not args.baseline.exists():
        print(
            f"FAIL: baseline file not found at '{args.baseline}'. "
            "A coverage ratchet has no floor to enforce without one.",
            file=sys.stderr,
        )
        return 2

    baseline_data = load_baseline(args.baseline)
    baseline_pct = float(baseline_data["combined_pct"])

    tolerance_pct = args.tolerance_pct
    if tolerance_pct is None:
        tolerance_pct = float(baseline_data.get("tolerance_pct", DEFAULT_TOLERANCE_PCT))

    combined_pct, details = compute_combined_pct(args.coverage_xml)
    threshold = baseline_pct - tolerance_pct

    print(f"BYS360 coverage ratchet: measured combined coverage = {combined_pct:.4f}%")
    print(
        f"  (lines {details['lines_covered']}/{details['lines_valid']} = "
        f"{details['line_pct']:.2f}%, branches {details['branches_covered']}/"
        f"{details['branches_valid']} = {details['branch_pct']:.2f}%)"
    )
    print(
        f"BYS360 coverage ratchet: baseline = {baseline_pct:.4f}% "
        f"(tolerance {tolerance_pct:.4f} pts -> pass threshold {threshold:.4f}%)"
    )

    if combined_pct + 1e-9 < threshold:
        print(
            "FAIL: combined coverage "
            f"{combined_pct:.4f}% is below the ratchet threshold {threshold:.4f}% "
            f"(baseline {baseline_pct:.4f}% - tolerance {tolerance_pct:.4f} pts). "
            "Coverage has regressed relative to the last recorded baseline in "
            f"'{args.baseline}'. This gate does not auto-lower the baseline for you -- "
            "either restore the missing coverage, or, if the drop is deliberate and "
            "reviewed, have a human update coverage_baseline.json with a documented reason.",
            file=sys.stderr,
        )
        return 1

    print(
        f"PASS: combined coverage {combined_pct:.4f}% meets or exceeds the ratchet "
        f"threshold {threshold:.4f}%. "
        "Note: this script never raises the stored baseline automatically, even though "
        "the measured value may be above it -- raising the floor is a separate, "
        "human-reviewed decision (edit coverage_baseline.json by hand if warranted)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
