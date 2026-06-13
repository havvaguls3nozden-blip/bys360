from __future__ import annotations

import json
import re
import sys
from pathlib import Path
import py_compile

project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
target = project_root / "app" / "services" / "cic" / "mail_scheduler_service.py"
checks = {
    "target_exists": target.exists(),
    "has_import_logging": False,
    "uses_logging": False,
    "import_before_first_use": False,
    "py_compile": False,
}

if target.exists():
    text = target.read_text(encoding="utf-8")
    lines = text.splitlines()
    import_positions = [i for i, line in enumerate(lines) if re.match(r"^\s*import\s+logging\s*(#.*)?$", line)]
    use_positions = [i for i, line in enumerate(lines) if ("logging.getLogger" in line or "logging." in line) and not re.match(r"^\s*import\s+logging\s*(#.*)?$", line)]
    checks["has_import_logging"] = bool(import_positions)
    checks["uses_logging"] = bool(use_positions)
    checks["import_before_first_use"] = bool(import_positions) and (not use_positions or min(import_positions) < min(use_positions))
    try:
        py_compile.compile(str(target), doraise=True)
        checks["py_compile"] = True
    except Exception as exc:  # pragma: no cover
        checks["py_compile_error"] = str(exc)

ok = all(checks.values())
print(json.dumps({"package": "BYS360_CIC_LOGGING_ORDER_HOTFIX_V2", "ok": ok, "checks": checks}, ensure_ascii=False, indent=2))
if not ok:
    raise SystemExit(1)
print("BYS360_CIC_LOGGING_ORDER_HOTFIX_V2_OK")
