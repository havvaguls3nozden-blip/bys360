# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, importlib.util, json, py_compile, subprocess, sys
from datetime import date
from pathlib import Path

PACKAGE = "performance_completion_phase11_period_scope_assignment_final"
VERSION = "V1"

REQUIRED_FILES = [
    "app/services/performance/phase11_period_scope_assignment_center.py",
    "app/services/performance/period_scope_assignment_service.py",
    "app/templates/performance/_phase11_period_scope_assignment_panel.html",
    "app/static/css/performance_completion_phase11_period_scope_assignment.css",
    "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE11_PERIOD_SCOPE_ASSIGNMENT_FINAL.md",
]

PY_FILES = [
    "app/services/performance/phase11_period_scope_assignment_center.py",
    "app/services/performance/period_scope_assignment_service.py",
]


def load_center(root: Path):
    path = root / "app/services/performance/phase11_period_scope_assignment_center.py"
    spec = importlib.util.spec_from_file_location("phase11_period_scope_assignment_center_check", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("phase11 center yüklenemedi")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def compile_files(root: Path) -> dict:
    errors = []
    for rel in PY_FILES:
        path = root / rel
        if not path.exists():
            errors.append({"file": rel, "error": "missing"})
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            errors.append({"file": rel, "error": str(exc)})
    return {"ok": not errors, "errors": errors}


def markers_check(root: Path) -> dict:
    items = []
    required = {
        "app/services/performance/phase11_period_scope_assignment_center.py": [
            "BYS360_PERFORMANCE_COMPLETION_PHASE11_PERIOD_SCOPE_ASSIGNMENT_FINAL",
            "BYS360_PERFORMANCE_COMPLETION_PHASE11_MULTI_PERIOD",
            "BYS360_PERFORMANCE_COMPLETION_PHASE11_OVERLAP_CONTROL",
            "BYS360_PERFORMANCE_COMPLETION_PHASE11_NO_FAKE_ASSIGNMENT",
            "phase11_assignment_precheck",
        ],
        "app/templates/performance/_phase11_period_scope_assignment_panel.html": [
            "BYS360_PERFORMANCE_COMPLETION_PHASE11_PERIOD_SCOPE_ASSIGNMENT_PANEL",
            "Çoklu Dönem ve Kapsam Kontrolü",
        ],
        "app/static/css/performance_completion_phase11_period_scope_assignment.css": [
            "BYS360_PERFORMANCE_COMPLETION_PHASE11_PERIOD_SCOPE_ASSIGNMENT_CSS",
        ],
    }
    for rel, markers in required.items():
        text = (root / rel).read_text(encoding="utf-8") if (root / rel).exists() else ""
        marker_result = {marker: marker in text for marker in markers}
        items.append({"file": rel, "ok": all(marker_result.values()), "markers": marker_result})
    return {"ok": all(item["ok"] for item in items), "items": items}


def smoke_policy(root: Path) -> dict:
    center = load_center(root)
    good = center.phase11_validate_period_scope({
        "name": "2026 Güvenlik Özel Dönemi",
        "period_type": "special",
        "scope_type": "category",
        "category": "Güvenlik",
        "start_date": "2026-01-01",
        "end_date": "2026-03-31",
    }).as_dict()
    bad_scope = center.phase11_validate_period_scope({
        "name": "Eksik Kategori",
        "period_type": "quarterly",
        "scope_type": "category",
        "start_date": "2026-01-01",
        "end_date": "2026-03-31",
    }).as_dict()
    bad_dates = center.phase11_validate_period_scope({
        "name": "Tarih Hatalı",
        "period_type": "monthly",
        "scope_type": "all",
        "start_date": "2026-03-31",
        "end_date": "2026-01-01",
    }).as_dict()
    personnel = [
        {"id": 1, "name": "A", "unit_id": 10, "parent_unit_id": 100, "performance_category": "Güvenlik"},
        {"id": 2, "name": "B", "unit_id": 11, "parent_unit_id": 100, "performance_category": "Temizlik"},
        {"id": 3, "name": "C", "unit_id": 10, "parent_unit_id": 101, "performance_category": "Güvenlik"},
    ]
    filtered_category = center.phase11_filter_personnel_by_scope(personnel, {"scope_type": "category", "category": "Güvenlik"})
    filtered_selected = center.phase11_filter_personnel_by_scope(personnel, {"scope_type": "selected_personnel", "selected_personnel_ids": [2]})
    precheck_ok = center.phase11_assignment_precheck({
        "name": "2026 Güvenlik Özel Dönemi",
        "period_type": "special",
        "scope_type": "category",
        "category": "Güvenlik",
        "start_date": "2026-01-01",
        "end_date": "2026-03-31",
    }, personnel).as_dict()
    precheck_missing_criteria = center.phase11_assignment_precheck({
        "name": "2026 Güvenlik Özel Dönemi",
        "period_type": "special",
        "scope_type": "category",
        "category": "Güvenlik",
        "start_date": "2026-01-01",
        "end_date": "2026-03-31",
    }, personnel, criteria_ok=False).as_dict()
    overlap = center.phase11_detect_period_overlap(
        {"start_date": date(2026, 1, 1), "end_date": date(2026, 3, 31), "personnel_ids": [1]},
        [{"id": 99, "start_date": date(2026, 2, 1), "end_date": date(2026, 2, 28), "status": "active", "personnel_ids": [1]}],
    ).as_dict()
    safe_rows = center.phase11_safe_assignment_rows(personnel, {"scope_type": "selected_personnel", "selected_personnel_ids": [2]})
    items = {
        "version": getattr(center, "BYS360_PERFORMANCE_COMPLETION_PHASE11_VERSION", "").endswith("v1"),
        "good_validation": good["ok"],
        "bad_scope_blocked": not bad_scope["ok"],
        "bad_dates_blocked": not bad_dates["ok"],
        "category_filter_count": len(filtered_category) == 2,
        "selected_filter_count": len(filtered_selected) == 1 and (filtered_selected[0].get("id") if isinstance(filtered_selected[0], dict) else getattr(filtered_selected[0], "id", None)) == 2,
        "precheck_ok": precheck_ok["ok"] and precheck_ok["eligible_personnel_count"] == 2,
        "missing_criteria_blocked": not precheck_missing_criteria["ok"] and precheck_missing_criteria["status"] == "missing_criteria",
        "overlap_detected": overlap["has_overlap"] and 99 in overlap["overlapping_period_ids"],
        "no_fake_assignment_rows": bool(safe_rows) and all(row.get("fake_assignment") is False for row in safe_rows),
        "technical_clean": not center.phase11_contains_visible_technical_language(center.phase11_clean_text("workflow endpoint debug")),
        "contract_settings": len(center.phase11_period_scope_contract().get("settings", [])) >= 8,
    }
    return {"ok": all(items.values()), "items": items, "precheck_ok": precheck_ok, "overlap": overlap}


def app_seed_check(root: Path) -> dict:
    code = """
from app import create_app
app = create_app()
with app.app_context():
    from app.services.performance.phase11_period_scope_assignment_center import seed_phase11_settings
    import json
    print(json.dumps(seed_phase11_settings(), ensure_ascii=False))
""".strip()
    proc = subprocess.run([sys.executable, "-c", code], cwd=str(root), text=True, capture_output=True)
    lines = (proc.stdout or "").strip().splitlines()
    payload = lines[-1] if lines else "{}"
    try:
        data = json.loads(payload)
    except Exception:
        data = {"ok": False, "stdout": proc.stdout, "stderr": proc.stderr, "returncode": proc.returncode}
    if proc.returncode != 0:
        data["ok"] = False
        data["stderr"] = proc.stderr
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--skip-app", action="store_true")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    result = {
        "package": PACKAGE,
        "version": VERSION,
        "project_root": str(root),
        "required_files": {"ok": True, "missing": [rel for rel in REQUIRED_FILES if not (root / rel).exists()]},
    }
    result["required_files"]["ok"] = not result["required_files"]["missing"]
    result["markers"] = markers_check(root)
    result["compile"] = compile_files(root)
    result["policy_smoke"] = smoke_policy(root)
    if not args.skip_app:
        result["app_seed_check"] = app_seed_check(root)
    else:
        result["app_seed_check"] = {"ok": True, "skipped": True}
    result["ok"] = all([
        result["required_files"]["ok"],
        result["markers"]["ok"],
        result["compile"]["ok"],
        result["policy_smoke"]["ok"],
        result["app_seed_check"].get("ok", False),
    ])
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    if result["ok"]:
        print("BYS360_PERFORMANCE_COMPLETION_PHASE11_PERIOD_SCOPE_ASSIGNMENT_FINAL_CHECK_OK")
    else:
        print("BYS360_PERFORMANCE_COMPLETION_PHASE11_PERIOD_SCOPE_ASSIGNMENT_FINAL_CHECK_FAIL")
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
