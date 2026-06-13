from __future__ import annotations

import argparse
import py_compile
from pathlib import Path

TARGET_REL = "app/api/mobile/routes.py"
ADAPTER_MARKER = "BYS360_P14F2_MOBILE_ROUTE_REGISTRAR_ADAPTER"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target = project_root / TARGET_REL

    print("BYS360_P14F2_MOBILE_API_ROUTE_REGISTRAR_ADAPTER_CHECK_START")
    print(f"project_root={project_root}")

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    text = target.read_text(encoding="utf-8", errors="ignore")
    py_compile.compile(str(target), doraise=True)

    old_bad_1 = "_register_mobile_performance_read_routes_v1(mobile_bp, globals())" in text
    old_bad_2 = "_register_mobile_performance_read_routes_v1(_bys360_mobile_utility_bp_v1, globals())" in text
    adapted = "_bys360_call_mobile_route_registrar_v1(_register_mobile_performance_read_routes_v1" in text
    adapter_present = ADAPTER_MARKER in text

    if old_bad_1 or old_bad_2 or not adapted or not adapter_present:
        raise SystemExit(
            f"P14F2_CHECK_FAIL old_bad_1={old_bad_1} old_bad_2={old_bad_2} "
            f"adapted={adapted} adapter_present={adapter_present}"
        )

    print(f"old_performance_mobile_bp_call_present={old_bad_1}")
    print(f"old_performance_resolved_two_arg_call_present={old_bad_2}")
    print(f"performance_read_adapted={adapted}")
    print(f"adapter_present={adapter_present}")
    print("compile_ok=True")
    print("BYS360_P14F2_MOBILE_API_ROUTE_REGISTRAR_ADAPTER_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
