from __future__ import annotations

import json
import py_compile
import re
import sys
from pathlib import Path


PACKAGE = "BYS360_CIC_LOGGING_IMPORT_HOTFIX_V1"


def _read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def main() -> int:
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    target = project_root / "app" / "services" / "cic" / "mail_scheduler_service.py"
    route = project_root / "app" / "communication" / "corporate_information_center_routes.py"

    checks = {
        "target_exists": target.exists(),
        "route_exists": route.exists(),
        "uses_logging_getLogger": False,
        "has_import_logging": False,
        "py_compile": False,
    }

    if target.exists():
        text = _read_text(target)
        checks["uses_logging_getLogger"] = "logging.getLogger" in text
        checks["has_import_logging"] = bool(
            re.search(r"(?m)^\s*import\s+logging\b", text)
            or re.search(r"(?m)^\s*from\s+logging\s+import\b", text)
        )
        try:
            py_compile.compile(str(target), doraise=True)
            checks["py_compile"] = True
        except Exception as exc:
            checks["py_compile_error"] = str(exc)

    ok = (
        checks["target_exists"]
        and checks["route_exists"]
        and checks["uses_logging_getLogger"]
        and checks["has_import_logging"]
        and checks["py_compile"]
    )

    print(json.dumps({"package": PACKAGE, "ok": ok, "checks": checks}, ensure_ascii=False, indent=2))
    if ok:
        print("BYS360_CIC_LOGGING_IMPORT_HOTFIX_V1_OK")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
