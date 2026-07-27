from __future__ import annotations

import importlib
import json
import os
import py_compile
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_PHASE3D_IMPORT_ROUTE_SMOKE_V1"
REPORT_REL = Path("reports/architecture/BYS360_PHASE3D_IMPORT_ROUTE_SMOKE_V1_REPORT.json")

TARGET_FILES = [
    "app/api/mobile/performance_routes.py",
    "app/api/mobile/services/performance_score_route_services.py",
    "app/api/mobile/services/performance_note_route_services.py",
    "app/api/mobile/services/performance_task_detail_route_services.py",
    "app/api/mobile/services/performance_summary_risk_route_services.py",
    "app/api/mobile/services/performance_compact_route_services.py",
]

SERVICE_MODULES = {
    "app.api.mobile.services.performance_score_route_services": [
        "phase3c_mobile_performance_task_score_form_service",
        "phase3c_mobile_performance_task_score_submit_service",
        "phase3c_mobile_performance_task_score_action_service",
    ],
    "app.api.mobile.services.performance_note_route_services": [
        "phase3c_mobile_performance_in_period_notes_v2853_service",
        "phase3c_mobile_performance_create_in_period_note_v2853_service",
        "phase3c_mobile_performance_note_scorecard_v2863a_service",
    ],
    "app.api.mobile.services.performance_task_detail_route_services": [
        "phase3c_mobile_performance_third_manager_service",
        "phase3c_mobile_performance_task_detail_service",
    ],
    "app.api.mobile.services.performance_summary_risk_route_services": [
        "phase3c_mobile_performance_full_feature_summary_service",
        "phase3c_mobile_performance_publish_preapproval_service",
        "phase3c_mobile_performance_risk_analysis_v2852_service",
    ],
    "app.api.mobile.services.performance_compact_route_services": [
        "phase3c_mobile_performance_approvals_service",
        "phase3c_mobile_performance_criteria_service",
        "phase3c_mobile_performance_in_period_notes_legacy_service",
    ],
}

EXPECTED_MOBILE_PERFORMANCE_ROUTES = [
    {"fragment": "/performance/summary", "method": "GET"},
    {"fragment": "/performance/periods/<int:period_id>", "method": "GET"},
    {"fragment": "/performance/approvals", "method": "GET"},
    {"fragment": "/performance/scorecards", "method": "GET"},
    {"fragment": "/performance/rules-summary", "method": "GET"},
    {"fragment": "/performance/criteria", "method": "GET"},
    {"fragment": "/performance/third-manager", "method": "GET"},
    {"fragment": "/performance/tasks/<int:assignment_id>", "method": "GET"},
    {"fragment": "/performance/tasks/<int:assignment_id>/score-form", "method": "GET"},
    {"fragment": "/performance/tasks/<int:assignment_id>/score-form", "method": "POST"},
    {"fragment": "/performance/tasks/<int:assignment_id>/score-action", "method": "POST"},
    {"fragment": "/performance/full-feature-summary", "method": "GET"},
    {"fragment": "/performance/president-approvals", "method": "GET"},
    {"fragment": "/performance/publish-preapproval", "method": "GET"},
    {"fragment": "/performance/history-archive", "method": "GET"},
    {"fragment": "/performance/in-period-notes", "method": "GET"},
    {"fragment": "/performance/development-suggestions", "method": "GET"},
    {"fragment": "/performance/reports", "method": "GET"},
    {"fragment": "/performance/risk-analysis", "method": "GET"},
    {"fragment": "/performance/in-period-notes/v2", "method": "GET"},
    {"fragment": "/performance/in-period-notes/v2", "method": "POST"},
    {"fragment": "/performance/note-scorecard", "method": "GET"},
]


def _compile_file(path: Path) -> dict[str, Any]:
    item: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "ok": False,
        "error": None,
    }

    if not path.exists():
        item["error"] = "file_not_found"
        return item

    try:
        py_compile.compile(str(path), doraise=True)
        item["ok"] = True
    except Exception as exc:
        item["error"] = repr(exc)

    return item


def _route_decorator_count(text: str) -> int:
    return len(re.findall(r"^@mobile_api_bp\.(?:get|post|route)\(", text, re.MULTILINE))


def _import_services(root: Path) -> dict[str, Any]:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    modules: dict[str, Any] = {}

    for module_name, expected_functions in SERVICE_MODULES.items():
        item: dict[str, Any] = {
            "module": module_name,
            "ok": False,
            "expected_functions": expected_functions,
            "functions_present": {},
            "error": None,
        }

        try:
            module = importlib.import_module(module_name)
            item["functions_present"] = {
                fn: callable(getattr(module, fn, None))
                for fn in expected_functions
            }
            item["ok"] = all(item["functions_present"].values())
        except Exception as exc:
            item["error"] = repr(exc)

        modules[module_name] = item

    return {
        "ok": all(item["ok"] for item in modules.values()),
        "modules": modules,
    }


def _app_factory_route_smoke(root: Path) -> dict[str, Any]:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    os.environ.setdefault("FLASK_ENV", "development")

    try:
        from app import create_app

        app = create_app()
        rules = []
        for rule in app.url_map.iter_rules():
            rules.append({
                "rule": str(rule.rule),
                "endpoint": str(rule.endpoint),
                "methods": sorted(m for m in (rule.methods or ()) if m not in {"HEAD", "OPTIONS"}),
            })

        expected_results = []
        for expected in EXPECTED_MOBILE_PERFORMANCE_ROUTES:
            matches = [
                r for r in rules
                if expected["fragment"] in r["rule"] and expected["method"] in r["methods"]
            ]
            expected_results.append({
                "fragment": expected["fragment"],
                "method": expected["method"],
                "matched": bool(matches),
                "matches": matches[:5],
            })

        return {
            "ok": all(item["matched"] for item in expected_results),
            "route_count": len(rules),
            "expected_mobile_performance_route_count": len(EXPECTED_MOBILE_PERFORMANCE_ROUTES),
            "expected_results": expected_results,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": repr(exc),
            "traceback_tail": traceback.format_exc()[-4000:],
        }


def run_checks(root: Path, write_report: bool = True) -> dict[str, Any]:
    route_path = root / "app/api/mobile/performance_routes.py"
    route_text = route_path.read_text(encoding="utf-8", errors="replace") if route_path.exists() else ""

    compile_results = {
        rel: _compile_file(root / rel)
        for rel in TARGET_FILES
    }

    service_import = _import_services(root)
    app_factory_smoke = _app_factory_route_smoke(root)

    result: dict[str, Any] = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "target_files": TARGET_FILES,
        "compile_results": compile_results,
        "compile_ok": all(item["ok"] for item in compile_results.values()),
        "route_path": "app/api/mobile/performance_routes.py",
        "route_lines": len(route_text.splitlines()),
        "route_decorator_count": _route_decorator_count(route_text),
        "route_decorator_count_ok": _route_decorator_count(route_text) == 22,
        "service_import": service_import,
        "app_factory_route_smoke": app_factory_smoke,
        "phase3d_import_route_smoke_ok": False,
    }

    result["phase3d_import_route_smoke_ok"] = bool(
        result["compile_ok"]
        and result["route_decorator_count_ok"]
        and result["service_import"]["ok"]
        and result["app_factory_route_smoke"]["ok"]
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
    print(json.dumps({
        "phase3d_import_route_smoke_ok": result["phase3d_import_route_smoke_ok"],
        "compile_ok": result["compile_ok"],
        "route_lines": result["route_lines"],
        "route_decorator_count": result["route_decorator_count"],
        "service_import_ok": result["service_import"]["ok"],
        "app_factory_route_smoke_ok": result["app_factory_route_smoke"]["ok"],
        "app_route_count": result["app_factory_route_smoke"].get("route_count"),
        "report": result.get("report"),
    }, ensure_ascii=False, indent=2))
    return 0 if result["phase3d_import_route_smoke_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
