from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_MIN_TOTAL = 21.08
DEFAULT_MIN_BRANCH = 6.69
def _load_coverage(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"coverage json not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(
    coverage_json: Path,
    min_total: float = DEFAULT_MIN_TOTAL,
    min_branch: float = DEFAULT_MIN_BRANCH,
) -> dict[str, Any]:
    data = _load_coverage(coverage_json)
    totals = data.get("totals") or {}

    total_percent = float(totals.get("percent_covered", 0.0))
    branch_percent = float(totals.get("percent_branches_covered", 0.0))

    total_ok = total_percent + 1e-9 >= float(min_total)
    branch_ok = branch_percent + 1e-9 >= float(min_branch)

    return {
        "ok": bool(total_ok and branch_ok),
        "coverage_json": str(coverage_json),
        "baseline": {
            "min_total_percent": float(min_total),
            "min_branch_percent": float(min_branch),
        },
        "actual": {
            "total_percent": total_percent,
            "branch_percent": branch_percent,
            "covered_lines": int(totals.get("covered_lines", 0)),
            "num_statements": int(totals.get("num_statements", 0)),
            "missing_lines": int(totals.get("missing_lines", 0)),
            "covered_branches": int(totals.get("covered_branches", 0)),
            "missing_branches": int(totals.get("missing_branches", 0)),
        },
        "checks": {
            "total_ok": bool(total_ok),
            "branch_ok": bool(branch_ok),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage-json", required=True)
    parser.add_argument("--min-total", type=float, default=DEFAULT_MIN_TOTAL)
    parser.add_argument("--min-branch", type=float, default=DEFAULT_MIN_BRANCH)
    args = parser.parse_args()

    report = build_report(
        Path(args.coverage_json),
        min_total=args.min_total,
        min_branch=args.min_branch,
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
