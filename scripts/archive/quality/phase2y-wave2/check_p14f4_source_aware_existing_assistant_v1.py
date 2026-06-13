from __future__ import annotations

import argparse
import json
from pathlib import Path

BASE_REL = "app/templates/base.html"
ASSISTANT_JS_REL = "app/static/js/bys360_assistant_module.js"
CACHE_VERSION = "assistant-restore-p14f4-existing"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    base = read_text(project_root / BASE_REL)
    js = read_text(project_root / ASSISTANT_JS_REL)

    result = {
        "base_has_root": "bys360-assistant-module-root" in base,
        "base_has_helper_script": "bys360_assistant_helpers_v1.js" in base,
        "base_has_module_script": "bys360_assistant_module.js" in base,
        "base_has_cache_bust_version": CACHE_VERSION in base,
        "assistant_js_contains_helper_wrapper": "BYS360AssistantHelpersV1" in js,
        "assistant_js_has_visibility_restore_marker": "BYS360_ASSISTANT_VISIBILITY_RESTORE_V31_1" in js,
        "assistant_js_line_count": len(js.splitlines()),
    }

    print("BYS360_P14F4_SOURCE_AWARE_ASSISTANT_RESTORE_CHECK_START")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result["base_has_root"]:
        raise SystemExit("P14F4_CHECK_FAIL base_has_root=False")
    if result["base_has_helper_script"]:
        raise SystemExit("P14F4_CHECK_FAIL base_has_helper_script=True")
    if not result["base_has_module_script"]:
        raise SystemExit("P14F4_CHECK_FAIL base_has_module_script=False")
    if not result["base_has_cache_bust_version"]:
        raise SystemExit("P14F4_CHECK_FAIL base_has_cache_bust_version=False")
    if result["assistant_js_contains_helper_wrapper"]:
        raise SystemExit("P14F4_CHECK_FAIL assistant_js_contains_helper_wrapper=True")

    print("BYS360_P14F4_SOURCE_AWARE_ASSISTANT_RESTORE_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
