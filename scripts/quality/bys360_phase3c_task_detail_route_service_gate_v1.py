from __future__ import annotations

import ast
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_PHASE3C_TASK_DETAIL_ROUTE_SERVICE_GATE_V1"
REPORT_REL = Path("reports/architecture/BYS360_PHASE3C_TASK_DETAIL_ROUTE_SERVICE_GATE_V1_REPORT.json")

ROUTE_REL = Path("app/api/mobile/performance_routes.py")
SERVICE_REL = Path("app/api/mobile/services/performance_task_detail_route_services.py")

TARGET_ROUTE_FUNCTIONS = [
    "mobile_performance_third_manager",
    "mobile_performance_task_detail",
]

TARGET_SERVICE_FUNCTIONS = [
    "phase3c_mobile_performance_third_manager_service",
    "phase3c_mobile_performance_task_detail_service",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _route_decorator_count(text: str) -> int:
    return len(re.findall(r"^@mobile_api_bp\.(?:get|post|route)\(", text, re.MULTILINE))


def _function_line_counts(text: str) -> dict[str, int]:
    if not text.strip():
        return {}
    tree = ast.parse(text)
    counts: dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            counts[node.name] = int((node.end_lineno or node.lineno) - node.lineno + 1)
    return counts


def _defined_functions(text: str) -> set[str]:
    if not text.strip():
        return set()
    tree = ast.parse(text)
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def run_checks(root: Path, write_report: bool = True) -> dict[str, Any]:
    route_path = root / ROUTE_REL
    service_path = root / SERVICE_REL

    route_text = _read(route_path)
    service_text = _read(service_path)

    route_counts = _function_line_counts(route_text)
    service_functions = _defined_functions(service_text)

    route_wrappers = {
        name: route_counts.get(name, 9999)
        for name in TARGET_ROUTE_FUNCTIONS
    }

    service_presence = {
        name: name in service_functions
        for name in TARGET_SERVICE_FUNCTIONS
    }

    result: dict[str, Any] = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "route_path": str(ROUTE_REL),
        "service_path": str(SERVICE_REL),
        "route_exists": route_path.exists(),
        "service_exists": service_path.exists(),
        "route_lines": len(route_text.splitlines()),
        "service_lines": len(service_text.splitlines()),
        "route_decorator_count": _route_decorator_count(route_text),
        "route_import_ok": "performance_task_detail_route_services" in route_text,
        "deps_function_ok": "def _phase3c_task_detail_route_deps(" in route_text,
        "route_wrappers": route_wrappers,
        "route_wrappers_small_ok": all(v <= 3 for v in route_wrappers.values()),
        "service_presence": service_presence,
        "service_logic_ok": all(token in service_text for token in [
            "PerformanceCriteria.query",
            "_v2822_due_label",
            "_v2822_can_view_assignment",
            "PerformanceWeightConfig.query",
            "_v2821_mode_text",
            "3. amir",
            "Süreç uyarısı",
        ]),
        "route_line_reduction_ok": len(route_text.splitlines()) < 1225,
        "task_detail_route_service_gate_ok": False,
    }

    result["task_detail_route_service_gate_ok"] = bool(
        result["route_exists"]
        and result["service_exists"]
        and result["route_decorator_count"] == 22
        and result["route_import_ok"]
        and result["deps_function_ok"]
        and result["route_wrappers_small_ok"]
        and result["service_logic_ok"]
        and result["route_line_reduction_ok"]
        and all(service_presence.values())
    )

    if write_report:
        report = root / REPORT_REL
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        result["report"] = str(report)

    return result


def main() -> int:
    root = Path.cwd()
    result = run_checks(root, write_report=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["task_detail_route_service_gate_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
