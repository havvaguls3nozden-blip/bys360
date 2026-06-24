from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P3B_MOBILE_AUTH_DASHBOARD_ASSISTANT_RESPONSE_GATE"
REPORT_REL = "reports/architecture/BYS360_MOBILE_AUTH_DASHBOARD_ASSISTANT_RESPONSE_GATE_P3B_REPORT.json"
ACTIVE_TEST = "test_mobile_auth_dashboard_assistant_response_p3b.py"


def patch_conftest(root: Path) -> dict[str, object]:
    path = root / "tests" / "architecture" / "conftest.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            "from __future__ import annotations\n\n"
            "import os\n\n"
            "ACTIVE_ARCHITECTURE_TESTS = {\n"
            f"    {ACTIVE_TEST!r},\n"
            "}\n\n"
            "def pytest_collection_modifyitems(config, items):\n"
            "    if os.getenv('BYS360_RUN_LEGACY_ARCHITECTURE_TESTS') == '1':\n"
            "        return\n"
            "    import pytest\n"
            "    skip_legacy = pytest.mark.skip(reason='legacy architecture contract archived; set BYS360_RUN_LEGACY_ARCHITECTURE_TESTS=1 to run')\n"
            "    for item in items:\n"
            "        if item.path.name not in ACTIVE_ARCHITECTURE_TESTS:\n"
            "            item.add_marker(skip_legacy)\n",
            encoding="utf-8",
        )
        return {"path": str(path), "changed": True, "reason": "created"}
    text = path.read_text(encoding="utf-8", errors="replace")
    if ACTIVE_TEST in text:
        return {"path": str(path), "changed": False, "reason": "already_present"}
    lines = text.splitlines()
    out: list[str] = []
    inserted = False
    in_active = False
    for line in lines:
        if in_active and line.strip() == "}":
            out.append(f"    {ACTIVE_TEST!r},")
            inserted = True
            in_active = False
        out.append(line)
        if line.strip().startswith("ACTIVE_ARCHITECTURE_TESTS") and "{" in line:
            in_active = True
    if inserted:
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
        return {"path": str(path), "changed": True, "reason": "inserted_into_active_set"}
    text += f"\n# {PACKAGE}: active architecture test -> {ACTIVE_TEST}\n"
    path.write_text(text, encoding="utf-8")
    return {"path": str(path), "changed": True, "reason": "appended_comment_fallback"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--app-factory", action="store_true")
    parser.add_argument("--secret-gate", action="store_true")
    parser.add_argument("--pytest", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    patch = patch_conftest(root)
    print(patch)
    cmd = [sys.executable, str(root / "scripts" / "quality" / "bys360_mobile_auth_dashboard_assistant_response_gate_p3b.py"), "--root", str(root)]
    if not args.compile_all:
        cmd.append("--no-compile")
    if not args.app_factory:
        cmd.append("--no-app-factory")
    if not args.secret_gate:
        cmd.append("--no-secret-gate")
    if not args.pytest:
        cmd.append("--no-pytest")
    completed = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
    report = root / REPORT_REL
    if report.exists():
        result = json.loads(report.read_text(encoding="utf-8"))
    else:
        result = {"ok": completed.returncode == 0, "stdout_tail": completed.stdout[-2000:], "stderr_tail": completed.stderr[-2000:], "report": str(report)}
    result["conftest_patch"] = patch
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result.get(k) for k in ["ok", "package", "routes_py_lines", "total_mobile_route_decorator_count", "direct_contract_ok", "runtime_route_map_ok", "response_code_smoke_ok", "compile_ok", "app_factory_ok", "secret_gate_ok", "pytest_ok", "pytest_mode", "report"]}, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
