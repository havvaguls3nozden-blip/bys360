from __future__ import annotations

import argparse
import json
import py_compile
from pathlib import Path

TARGET_REL = "app/api/mobile/routes.py"
OLD_CALL = "_register_mobile_utility_routes_v1(mobile_bp, globals())"
NEW_CALL = "_register_mobile_utility_routes_v1(_bys360_mobile_utility_bp_v1, globals())"
MARKER = "BYS360_P14F1_MOBILE_BLUEPRINT_RESOLVER"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target = project_root / TARGET_REL

    print("BYS360_P14F1_MOBILE_API_BLUEPRINT_NAME_FIX_CHECK_START")
    print(f"project_root={project_root}")

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    text = target.read_text(encoding="utf-8", errors="ignore")
    old_present = OLD_CALL in text
    new_present = NEW_CALL in text
    marker_present = MARKER in text

    py_compile.compile(str(target), doraise=True)

    result = {
        "target": TARGET_REL,
        "old_call_present": old_present,
        "new_call_present": new_present,
        "resolver_marker_present": marker_present,
        "compile_ok": True,
    }

    if old_present or not new_present or not marker_present:
        raise SystemExit("P14F1_CHECK_FAIL " + json.dumps(result, ensure_ascii=False))

    print(f"old_call_present={old_present}")
    print(f"new_call_present={new_present}")
    print(f"resolver_marker_present={marker_present}")
    print("compile_ok=True")
    print("BYS360_P14F1_MOBILE_API_BLUEPRINT_NAME_FIX_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
