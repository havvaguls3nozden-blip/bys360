# -*- coding: utf-8 -*-
"""P5D Android responsive release suite gate."""

from pathlib import Path


def test_android_responsive_release_suite_p5d_files_exist():
    root = Path(__file__).resolve().parents[2]
    assert (root / "scripts/quality/bys360_android_responsive_release_suite_gate_p5d.py").exists()
