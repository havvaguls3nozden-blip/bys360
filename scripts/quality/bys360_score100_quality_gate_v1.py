#!/usr/bin/env python3
"""
BYS360 SCORE 100 QUALITY GATE V1 - compatibility shim.

CONTEXT (2026-07-24, Campaign 1B / Agent 2 - Score100 Workflow Repair):
The real implementation of this gate was moved to
`scripts/archive/pre_handover_20260708/quality/bys360_score100_quality_gate_v1.py`
by commit 4f41319 ("chore: archive inactive handover scripts and clean repo
noise", 2026-07-08) as part of a 90-file bulk archival sweep. That sweep did
not update `.github/workflows/bys360-score100-quality-gate-v1.yml` or
`scripts/windows/repair_bys360_score100_quality_gate_v1.ps1`, both of which
still hard-require a script at THIS path - so the workflow has been broken
(fails at the .ps1 "Gate script bulunamadi" check) since that commit.

This shim restores the broken reference WITHOUT physically un-archiving the
file (the archival decision itself is left intact) and WITHOUT touching the
workflow YAML or the .ps1 wrapper. It is a pure, location-transparent
delegate: all path resolution inside the real script is driven by its own
--project-root argument, not by where this file lives, so delegating here is
behaviorally identical to running the archived script directly.

Campaign 2 follow-up recommended: an evidence review found this workflow's
checks are now largely covered - and in several cases (ruff, pip-audit,
TCKN encryption behavior, broad-except budget) covered more strictly - by
scripts/quality/bys360_secret_repo_gate.py, scripts/quality/bys360_quality9_ci_gate.py,
scripts/quality/bys360_ops_audit.py and the tests/quality pytest suite that
already run in .github/workflows/bys360-ci.yml. The two checks that are NOT
duplicated elsewhere are: (1) the Android key.properties.example cleartext
scan, and (2) the meta-check that
tests/quality/test_app_factory_registers_routes_without_duplicate_endpoints.py
exists and is not skip-guarded. Campaign 2 should decide whether to keep this
workflow for just those two checks, fold them into bys360-ci.yml, or retire
this workflow outright once a decision is made.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

_ARCHIVED_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "archive"
    / "pre_handover_20260708"
    / "quality"
    / "bys360_score100_quality_gate_v1.py"
)


def main() -> int:
    if not _ARCHIVED_SCRIPT.exists():
        print(
            f"Gate script bulunamadi (archived konum): {_ARCHIVED_SCRIPT}",
            file=sys.stderr,
        )
        return 2
    # Delegates with run_name="__main__" so the archived script's own
    # `if __name__ == "__main__": raise SystemExit(main())` executes exactly
    # as if it were invoked directly; its SystemExit propagates through here.
    runpy.run_path(str(_ARCHIVED_SCRIPT), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
