# -*- coding: utf-8 -*-
"""
P5C targeted Android responsive templates gate.
"""

from pathlib import Path


def test_android_responsive_targeted_templates_p5c_files_exist():
    root = Path(__file__).resolve().parents[2]
    assert (root / "scripts/quality/bys360_android_responsive_targeted_templates_gate_p5c.py").exists()
