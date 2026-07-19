# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATIC_JS = ROOT / "app" / "static" / "js"

ASSISTANT_SPLIT_FILES = [
    "bys360_assistant_module.js",
    "bys360_assistant_module_engines_v12_v19.js",
    "bys360_assistant_module_screen_agents_v20_v23.js",
    "bys360_assistant_module_memory_v30.js",
]


def test_assistant_js_split_assets_are_under_score100_large_file_limit():
    for name in ASSISTANT_SPLIT_FILES:
        path = STATIC_JS / name
        assert path.exists(), name
        assert path.stat().st_size < 250_000, f"{name} is too large: {path.stat().st_size}"


def test_assistant_js_split_load_order_is_preserved_in_base_template():
    base = (ROOT / "app" / "templates" / "base.html").read_text(encoding="utf-8")
    positions = [base.index(f"js/{name}") for name in ASSISTANT_SPLIT_FILES]
    assert positions == sorted(positions)


def test_assistant_js_split_expected_markers_exist():
    expected = {
        "bys360_assistant_module.js": "window.BYS360AssistantModule",
        "bys360_assistant_module_engines_v12_v19.js": "window.BYS360AssistantV12",
        "bys360_assistant_module_screen_agents_v20_v23.js": "window.BYS360AssistantScreenMapV20",
        "bys360_assistant_module_memory_v30.js": "window.BYS360AssistantStableScrollMemoryV30",
    }
    for name, marker in expected.items():
        body = (STATIC_JS / name).read_text(encoding="utf-8", errors="replace")
        assert marker in body
