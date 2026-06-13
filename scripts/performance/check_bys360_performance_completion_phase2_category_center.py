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
    "app/services/performance/phase2_category_center.py",
    "app/services/personnel/categories.py",
    "app/services/personnel/excel_import.py",
    "app/services/performance/category_stats.py",
    "app/models/core_models.py",
    "app/admin/routes.py",
    "app/admin/ops_routes.py",
    "app/performance/v2_1_2_category_routes.py",
    "app/performance/v2_1_3_personnel_category_card_routes.py",
    "app/performance/v2_1_4_category_scope_routes.py",
    "app/performance/v2_1_5_category_period_scope_routes.py",
    "app/performance/v2_1_6_category_period_integration_routes.py",
]

COMPILE_FILES = [
    "app/services/performance/phase2_category_center.py",
    "app/services/personnel/categories.py",
    "app/services/personnel/excel_import.py",
    "app/services/performance/category_stats.py",
    "app/admin/routes.py",
    "app/admin/ops_routes.py",
    "app/performance/v2_1_2_category_routes.py",
    "app/performance/v2_1_3_personnel_category_card_routes.py",
    "app/performance/v2_1_4_category_scope_routes.py",
    "app/performance/v2_1_5_category_period_scope_routes.py",
    "app/performance/v2_1_6_category_period_integration_routes.py",
]

MARKERS = {
    "app/services/performance/phase2_category_center.py": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_CENTER",
        "PRIVACY_NOTE",
        "PHASE2_SETTING_ROWS",
    ],
    "app/services/personnel/categories.py": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE2_PERSONNEL_CATEGORY_SERVICE",
        "assign_user_performance_category",
        "get_user_personnel_category_label",
    ],
    "app/models/core_models.py": [
        "class PersonnelCategory",
        "personnel_category",
        "performance_category_id",
    ],
    "app/services/personnel/excel_import.py": [
        "PERSONNEL_EXCEL_CATEGORY_ALIASES",
        "personnel_category",
    ],
    "app/admin/routes.py": [
        "personnel_category_options",
        "assign_user_performance_category",
        "BYS360_PERFORMANCE_COMPLETION_PHASE2_ADMIN_PERSONNEL_CATEGORY_MARKER",
    ],
    "app/admin/ops_routes.py": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE2_IMPORT_CATEGORY_MARKER",
        "personnel_category",
    ],
    "app/services/performance/category_stats.py": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_PRIVACY_MARKER",
        "detail_visible",
        "person_detail_visible",
    ],
}

UNSAFE_AVERAGE_KEYS = {"rows", "users", "employees", "personnel", "details", "person_details"}


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


class DummyUser:
    def __init__(self, category: str, score: float):
        self.personnel_category = category
        self.performance_category = None
        self.id = 1000
        self.final_score = score


class DummyEvaluation:
    def __init__(self, category: str, score: float):
        self.user = DummyUser(category, score)
        self.final_score = score
        self.personnel_category = category


def phase2_smoke(root: Path) -> dict[str, Any]:
    try:
        module = load_module_from_file(root, "app/services/performance/phase2_category_center.py", "bys360_phase2_category_center_direct")
        summary = module.category_average_without_person_detail(
            [
                DummyEvaluation("Güvenlik", 80),
                DummyEvaluation("Güvenlik", 90),
                DummyEvaluation("Temizlik", 70),
            ],
            "guvenlik",
        )
        contract = module.phase2_static_contract()
        smoke = {
            "version_flag": getattr(module, "BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_CENTER", False) is True,
            "default_category_count": len(getattr(module, "DEFAULT_CATEGORY_LABELS", ())) >= 6,
            "guvenlik_alias": module.normalize_category_label("guvenlik") == "Güvenlik",
            "temizlik_alias": module.normalize_category_label("Temizlik") == "Temizlik",
            "key_conversion": module.category_key_from_label("Deneme Süreli Personel") == "deneme_sureli_personel",
            "import_alias": "performans kategorisi" in module.import_aliases(),
            "privacy_detail_false": summary.get("detail_visible") is False and summary.get("person_detail_visible") is False,
            "privacy_average": summary.get("average_score") == 85.0,
            "no_unsafe_keys": not any(key in summary for key in UNSAFE_AVERAGE_KEYS),
            "settings_catalog": len(contract.get("settings") or []) >= 5,
        }
        return {"ok": all(smoke.values()), "items": smoke, "summary": summary, "contract": contract}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def app_check(root: Path) -> dict[str, Any]:
    sys.path.insert(0, str(root))
    try:
        from app import create_app
        from app.extensions import db
        from app.services.performance.phase2_category_center import DEFAULT_CATEGORY_LABELS, seed_phase2_category_center
        from app.services.personnel.categories import get_personnel_category_options

        app = create_app()
        with app.app_context():
            seed_result = seed_phase2_category_center(commit=True)
            options = get_personnel_category_options(db.session)
            option_ok = all(label in options for label in DEFAULT_CATEGORY_LABELS)
            table_names = []
            try:
                from sqlalchemy import inspect

                inspector = inspect(db.engine)
                table_names = [name for name in ("personnel_categories", "performance_personnel_categories", "performance_personnel_category_assignments") if inspector.has_table(name)]
            except Exception:
                table_names = []
            return {
                "ok": bool(seed_result.get("ok")) and option_ok,
                "seed": seed_result,
                "options": options,
                "required_options_ok": option_ok,
                "detected_tables": table_names,
            }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--app-check", action="store_true", help="Flask app bağlamında DB seed ve seçenek kontrolü çalıştırır")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    result: dict[str, Any] = {
        "package": "performance_completion_phase2_category_center",
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
    result["phase2_smoke"] = phase2_smoke(root)
    result["app_check"] = app_check(root) if args.app_check else {"ok": True, "skipped": True}

    result["ok"] = all([
        result["required_files"].get("ok"),
        result["markers"].get("ok"),
        result["compile"].get("ok"),
        result["phase2_smoke"].get("ok"),
        result["app_check"].get("ok"),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["ok"]:
        print("BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_CENTER_OK")
        return 0
    print("BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_CENTER_FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
