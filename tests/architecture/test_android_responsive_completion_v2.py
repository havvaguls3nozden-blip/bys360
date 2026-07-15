from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECK_SCRIPT = (
    ROOT
    / "scripts"
    / "quality"
    / "check_bys360_android_responsive_completion_v2.py"
)


def test_android_responsive_completion_v2() -> None:
    assert CHECK_SCRIPT.is_file(), CHECK_SCRIPT

    result = subprocess.run(
        [
            sys.executable,
            str(CHECK_SCRIPT),
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=180,
    )

    assert result.returncode == 0, (
        result.stdout
        + result.stderr
    )
