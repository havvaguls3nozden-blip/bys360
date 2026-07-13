from __future__ import annotations

import pytest

# -*- coding: utf-8 -*-

import json
import subprocess
import sys
from pathlib import Path


def test_android_responsive_core_styles_gate_p5b() -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "quality" / "bys360_android_responsive_core_styles_gate_p5b.py"
    report_path = (
        root
        / "reports"
        / "architecture"
        / "BYS360_ANDROID_RESPONSIVE_CORE_STYLES_GATE_P5B_REPORT.json"
    )
    before_report = (
        report_path.read_bytes()
        if report_path.exists()
        else None
    )
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--root",
            str(root),
            "--no-write-report",
        ],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    after_report = (
        report_path.read_bytes()
        if report_path.exists()
        else None
    )

    assert after_report == before_report
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["android_responsive_core_styles_gate_ok"] is True
    assert data["responsive_hardening_ok"] is True
    assert data["p5a_baseline_report_ok"] is True
    assert data["android_core_css_ok"] is True
    assert data["base_template_link_ok"] is True
    assert data["core_css_media_query_count"] >= 5
    assert data["direct_contract_ok"] is True

pytestmark = pytest.mark.mobile
