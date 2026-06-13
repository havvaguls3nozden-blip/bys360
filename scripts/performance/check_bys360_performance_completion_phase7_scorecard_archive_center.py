# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, importlib.util, json, py_compile, subprocess, sys
from datetime import datetime
from pathlib import Path

PACKAGE = "performance_completion_phase7_scorecard_archive_center"
VERSION = "V1"

REQUIRED_FILES = [
    "app/services/performance/phase7_scorecard_archive_center.py",
    "app/services/performance/scorecard_archive_service.py",
    "app/services/performance/scorecard_archive_import.py",
    "app/services/performance/archive_visibility_policy.py",
    "app/templates/performance/_phase7_scorecard_archive_panel.html",
    "app/static/css/performance_completion_phase7_scorecard_archive.css",
    "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE7_SCORECARD_ARCHIVE_CENTER.md",
]

MARKERS = {
    "app/services/performance/phase7_scorecard_archive_center.py": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE7_SCORECARD_ARCHIVE_CENTER",
        "BYS360_PERFORMANCE_COMPLETION_PHASE7_OWN_HISTORY_ONLY",
        "BYS360_PERFORMANCE_COMPLETION_PHASE7_SCOPE_VISIBILITY",
        "BYS360_PERFORMANCE_COMPLETION_PHASE7_IMPORT_VALIDATION",
        "BYS360_PERFORMANCE_COMPLETION_PHASE7_NO_PERSON_DETAIL_IN_AVERAGE",
        "validate_phase7_archive_record",
        "resolve_phase7_archive_visibility",
        "calculate_phase7_archive_summary",
    ],
    "app/services/performance/scorecard_archive_service.py": ["BYS360_PERFORMANCE_COMPLETION_PHASE7_ARCHIVE_SERVICE_BRIDGE"],
    "app/services/performance/scorecard_archive_import.py": ["BYS360_PERFORMANCE_COMPLETION_PHASE7_ARCHIVE_IMPORT_BRIDGE"],
    "app/services/performance/archive_visibility_policy.py": ["BYS360_PERFORMANCE_COMPLETION_PHASE7_ARCHIVE_VISIBILITY_BRIDGE"],
    "app/templates/performance/_phase7_scorecard_archive_panel.html": ["BYS360_PERFORMANCE_COMPLETION_PHASE7_SCORECARD_ARCHIVE_TEMPLATE"],
}

TARGET_TEMPLATES = [
    "app/templates/performance_scorecard_detail.html",
    "app/templates/performance_v2_phase5_scorecard.html",
    "app/templates/scorecard.html",
    "app/templates/performance/president_approval_scorecard.html",
    "app/templates/performance/president_approval_scorecard_v2.html",
    "app/templates/performance/president_card_review.html",
    "app/templates/performance/personnel_scorecard_archive.html",
    "app/templates/performance/scorecard_archive.html",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def load_center(root: Path):
    path = root / "app/services/performance/phase7_scorecard_archive_center.py"
    spec = importlib.util.spec_from_file_location("phase7_scorecard_archive_center_check", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def smoke_policy(root: Path) -> dict:
    center = load_center(root)
    valid = center.validate_phase7_archive_record({"sicil_no": "1001", "ad_soyad": "Test Personel", "yil": 2025, "donem": "2025 Yıllık", "puan": "88,5", "kaynak": "2025 cetveli"})
    invalid = center.validate_phase7_archive_record({"sicil_no": "", "yil": 2025, "donem": "", "puan": 120})
    own = center.resolve_phase7_archive_visibility(role="personel", current_user_id=7, record_user_id=7)
    other = center.resolve_phase7_archive_visibility(role="personel", current_user_id=7, record_user_id=8)
    manager = center.resolve_phase7_archive_visibility(role="koordinatör", same_scope=True, current_user_id=1, record_user_id=8)
    admin_import = center.resolve_phase7_archive_visibility(role="admin", action="import")
    summary = center.calculate_phase7_archive_summary([{"score": 65, "year": 2024, "full_name": "A"}, {"score": 92, "year": 2025, "full_name": "B"}])
    filtered = center.filter_phase7_archive_records([{"user_id": 7, "full_name": "A", "registry_no": "1", "score": 80}, {"user_id": 8, "full_name": "B", "registry_no": "2", "score": 90}], current_user_id=7, role="personel")
    contract = center.phase7_archive_contract()
    items = {
        "version": center.BYS360_PERFORMANCE_COMPLETION_PHASE7_VERSION == "performance-completion-phase7-scorecard-archive-center-v1",
        "valid_record": valid.ok and valid.normalized["score"] == 88.5,
        "invalid_record": (not invalid.ok) and bool(invalid.errors),
        "own_history": own.can_view and own.scope == "kendi_gecmisi" and own.show_person_detail is False,
        "other_blocked": other.can_view is False,
        "manager_scope": manager.can_view and manager.scope == "yetkili_kapsam",
        "admin_import": admin_import.can_import and admin_import.can_edit,
        "summary_no_detail": summary["person_details_included"] is False and summary["average_score"] == 78.5,
        "filtered_self_only": len(filtered) == 1 and "registry_no" not in filtered[0],
        "required_columns": "sicil_no" in center.phase7_required_import_columns(),
        "contract": bool(contract.get("markers", {}).get("no_person_detail_in_average")),
    }
    return {"ok": all(items.values()), "items": items, "valid": valid.as_dict(), "summary": summary, "contract": contract}


def app_check(root: Path) -> dict:
    code = """
from app import create_app
app = create_app()
with app.app_context():
    from app.services.performance.phase7_scorecard_archive_center import seed_phase7_scorecard_archive_settings
    import json
    print(json.dumps(seed_phase7_scorecard_archive_settings(), ensure_ascii=False))
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
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    result = {
        "package": PACKAGE,
        "version": VERSION,
        "project_root": str(root),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "required_files": {"ok": True, "missing": []},
        "markers": {"ok": True, "items": []},
        "compile": {"ok": True, "errors": []},
        "templates": {"ok": True, "items": []},
        "policy_smoke": None,
        "app_check": None,
        "ok": False,
    }
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            result["required_files"]["ok"] = False
            result["required_files"]["missing"].append(rel)
    for rel, needles in MARKERS.items():
        text = read(root / rel) if (root / rel).exists() else ""
        status = {needle: (needle in text) for needle in needles}
        result["markers"]["items"].append({"file": rel, "ok": all(status.values()), "markers": status})
    result["markers"]["ok"] = all(item["ok"] for item in result["markers"]["items"])
    for rel in [
        "app/services/performance/phase7_scorecard_archive_center.py",
        "app/services/performance/scorecard_archive_service.py",
        "app/services/performance/scorecard_archive_import.py",
        "app/services/performance/archive_visibility_policy.py",
    ]:
        if not (root / rel).exists():
            continue
        try:
            py_compile.compile(str(root / rel), doraise=True)
        except Exception as exc:
            result["compile"]["ok"] = False
            result["compile"]["errors"].append({"file": rel, "error": str(exc)})
    for rel in TARGET_TEMPLATES:
        path = root / rel
        if not path.exists():
            result["templates"]["items"].append({"file": rel, "exists": False, "bound": True})
            continue
        text = read(path)
        bound = "performance/_phase7_scorecard_archive_panel.html" in text or "BYS360_PERFORMANCE_COMPLETION_PHASE7_TEMPLATE_BOUND" in text
        result["templates"]["items"].append({"file": rel, "exists": True, "bound": bound})
    result["templates"]["ok"] = all(item["bound"] for item in result["templates"]["items"])
    try:
        result["policy_smoke"] = smoke_policy(root)
    except Exception as exc:
        result["policy_smoke"] = {"ok": False, "error": str(exc)}
    result["app_check"] = app_check(root)
    result["ok"] = all([
        result["required_files"]["ok"],
        result["markers"]["ok"],
        result["compile"]["ok"],
        result["templates"]["ok"],
        bool(result["policy_smoke"].get("ok")),
        bool(result["app_check"].get("ok")),
    ])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("BYS360_PERFORMANCE_COMPLETION_PHASE7_SCORECARD_ARCHIVE_CENTER_CHECK_OK" if result["ok"] else "BYS360_PERFORMANCE_COMPLETION_PHASE7_SCORECARD_ARCHIVE_CENTER_CHECK_FAIL")
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
