# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import importlib.util
import json
import py_compile
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REQUIRED_FILES = [
    "app/services/performance/completion_phase3_visibility_scope.py",
    "app/services/performance/phase3_backend_route_guard.py",
    "app/services/performance/phase3_role_matrix.py",
    "app/services/settings/effective_menu.py",
    "app/route_support.py",
]

COMPILE_FILES = REQUIRED_FILES + [
    "app/models/core_models.py",
]

MARKERS = {
    "app/services/performance/completion_phase3_visibility_scope.py": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE3_VISIBILITY_SCOPE",
        "BYS360_PERFORMANCE_COMPLETION_PHASE3_BACKEND_SCOPE_CENTER",
        "BYS360_PERFORMANCE_COMPLETION_PHASE3_MENU_ROUTE_LOCK",
        "PERFORMANCE_MENU_POLICY",
        "category_average_without_person_detail",
    ],
    "app/services/performance/phase3_backend_route_guard.py": [
        "BYS360_PHASE3_3_BACKEND_ROUTE_CONTROL",
        "BYS360_PERFORMANCE_COMPLETION_PHASE3_BACKEND_GUARD_DELEGATED",
    ],
    "app/services/performance/phase3_role_matrix.py": [
        "BYS360_PHASE3_1_ROLE_MATRIX",
        "get_phase3_visibility_profile",
    ],
    "app/services/settings/effective_menu.py": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE3_EFFECTIVE_MENU_BRIDGE",
        "apply_phase3_menu_visibility",
    ],
    "app/route_support.py": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE3_ROUTE_SUPPORT_BRIDGE",
        "Bu sayfaya erişim yetkiniz bulunmamaktadır",
    ],
}


class DummyUser:
    def __init__(self, role: str, user_id: int = 1, authenticated: bool = True):
        self.role = role
        self.id = user_id
        self.is_authenticated = authenticated


class DummyEvaluation:
    def __init__(self, employee_id: int):
        self.employee_id = employee_id


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def compile_required(root: Path) -> dict[str, Any]:
    errors = []
    for rel in COMPILE_FILES:
        path = root / rel
        if not path.exists() or path.suffix != ".py":
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            errors.append({"file": rel, "error": str(exc)})
    return {"ok": not errors, "errors": errors}


def load_module_from_file(root: Path, rel: str, name: str):
    path = root / rel
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"{rel} yüklenemedi")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def phase3_smoke(root: Path) -> dict[str, Any]:
    try:
        module = load_module_from_file(
            root,
            "app/services/performance/completion_phase3_visibility_scope.py",
            "bys360_phase3_visibility_center_direct",
        )
        # DB/app yokken güvenli smoke için kapsam üreticileri monkeypatch edilir.
        module._all_non_admin_user_ids = lambda: {1, 2, 3, 4}
        module._scope_context_employee_ids = lambda user: {2, 3}

        personel = DummyUser("personel", 10)
        coordinator = DummyUser("koordinator", 20)
        group_head = DummyUser("grup_baskani", 30)
        president = DummyUser("baskan", 40)
        admin = DummyUser("admin", 50)

        personel_visibility = module.apply_phase3_menu_visibility(
            {
                "performance_scorecard": True,
                "my_performance_comparison": True,
                "performance_reports": True,
                "performance_task_management": True,
                "performance_president_approvals": True,
            },
            personel,
        )
        admin_visibility = module.apply_phase3_menu_visibility(
            {"performance_task_management": True, "performance_president_approvals": True},
            admin,
        )
        contract = module.phase3_static_contract()
        smoke = {
            "version_flag": getattr(module, "BYS360_PERFORMANCE_COMPLETION_PHASE3_VISIBILITY_SCOPE", False) is True,
            "personel_role": module.resolve_visibility_role_key(personel) == "personel",
            "coordinator_role": module.resolve_visibility_role_key(coordinator) == "koordinator",
            "group_head_role": module.resolve_visibility_role_key(group_head) == "grup_baskani",
            "president_global": module.build_visibility_profile(president).can_view_global is True,
            "admin_technical": module.build_visibility_profile(admin).can_manage_visibility is True,
            "personel_own_only": module.phase3_allowed_employee_ids(personel) == {10},
            "personel_cannot_other": module.phase3_can_view_employee(personel, 11) is False,
            "coordinator_scoped": module.phase3_allowed_employee_ids(coordinator) == {2, 3},
            "admin_global_ids": module.phase3_allowed_employee_ids(admin) == {1, 2, 3, 4},
            "personel_category_average_ok": module.phase3_can_view_category_average(personel) is True,
            "personel_category_detail_blocked": module.phase3_can_view_category_average(personel, include_person_details=True) is False,
            "personel_menu_scorecard": personel_visibility.get("performance_scorecard") is True,
            "personel_menu_report_blocked": personel_visibility.get("performance_reports") is False,
            "personel_menu_technical_blocked": personel_visibility.get("performance_task_management") is False,
            "admin_menu_technical_ok": admin_visibility.get("performance_task_management") is True,
            "denied_context": module.access_denied_context().get("message") == module.ACCESS_DENIED_MESSAGE,
            "settings_catalog": len(contract.get("settings") or []) >= 5,
            "menu_policy_catalog": len(contract.get("menu_policy") or {}) >= 10,
        }
        return {"ok": all(smoke.values()), "items": smoke, "contract": contract}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def app_check(root: Path) -> dict[str, Any]:
    sys.path.insert(0, str(root))
    try:
        from app import create_app
        from app.services.performance.completion_phase3_visibility_scope import seed_phase3_visibility_center, phase3_static_contract

        app = create_app()
        with app.app_context():
            seed_result = seed_phase3_visibility_center(commit=True)
            contract = phase3_static_contract()
            return {
                "ok": bool(seed_result.get("ok")) and len(contract.get("settings") or []) >= 5,
                "seed": seed_result,
                "setting_count": len(contract.get("settings") or []),
            }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--app-check", action="store_true", help="Flask app bağlamında DB seed ve ayar kontrolü çalıştırır")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    result: dict[str, Any] = {
        "package": "performance_completion_phase3_visibility_center",
        "version": "V1",
        "project_root": str(root),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    missing = [rel for rel in REQUIRED_FILES if not (root / rel).exists()]
    result["required_files"] = {"ok": not missing, "missing": missing}

    marker_results = []
    for rel, markers in MARKERS.items():
        text_value = read_text(root / rel) if (root / rel).exists() else ""
        marker_results.append({"file": rel, "ok": all(marker in text_value for marker in markers), "markers": {marker: marker in text_value for marker in markers}})
    result["markers"] = {"ok": all(item["ok"] for item in marker_results), "items": marker_results}

    result["compile"] = compile_required(root)
    result["phase3_smoke"] = phase3_smoke(root)
    result["app_check"] = app_check(root) if args.app_check else {"ok": True, "skipped": True}

    result["ok"] = all([
        result["required_files"].get("ok"),
        result["markers"].get("ok"),
        result["compile"].get("ok"),
        result["phase3_smoke"].get("ok"),
        result["app_check"].get("ok"),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["ok"]:
        print("BYS360_PERFORMANCE_COMPLETION_PHASE3_VISIBILITY_CENTER_OK")
        return 0
    print("BYS360_PERFORMANCE_COMPLETION_PHASE3_VISIBILITY_CENTER_FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
