# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, importlib.util, json, py_compile, subprocess, sys
from datetime import datetime
from pathlib import Path

PACKAGE = "performance_completion_phase8_midterm_feedback_center"
VERSION = "V1"

REQUIRED_FILES = [
    "app/services/performance/phase8_midterm_feedback_center.py",
    "app/services/performance/midterm_feedback_service.py",
    "app/services/performance/interim_feedback_policy.py",
    "app/services/performance/scorecard_midterm_notes.py",
    "app/templates/performance/_phase8_midterm_feedback_panel.html",
    "app/static/css/performance_completion_phase8_midterm_feedback.css",
    "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE8_MIDTERM_FEEDBACK_CENTER.md",
]

MARKERS = {
    "app/services/performance/phase8_midterm_feedback_center.py": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE8_MIDTERM_FEEDBACK_CENTER",
        "BYS360_PERFORMANCE_COMPLETION_PHASE8_NO_AUTO_SCORE",
        "BYS360_PERFORMANCE_COMPLETION_PHASE8_EVALUATOR_REMINDER",
        "BYS360_PERFORMANCE_COMPLETION_PHASE8_SCORECARD_CONTROLLED_VISIBILITY",
        "validate_phase8_midterm_note",
        "resolve_phase8_midterm_visibility",
        "build_phase8_evaluator_reminders",
        "build_phase8_scorecard_summary",
    ],
    "app/services/performance/midterm_feedback_service.py": ["BYS360_PERFORMANCE_COMPLETION_PHASE8_MIDTERM_FEEDBACK_SERVICE_BRIDGE"],
    "app/services/performance/interim_feedback_policy.py": ["BYS360_PERFORMANCE_COMPLETION_PHASE8_INTERIM_FEEDBACK_POLICY_BRIDGE"],
    "app/services/performance/scorecard_midterm_notes.py": ["BYS360_PERFORMANCE_COMPLETION_PHASE8_SCORECARD_NOTES_BRIDGE"],
    "app/templates/performance/_phase8_midterm_feedback_panel.html": ["BYS360_PERFORMANCE_COMPLETION_PHASE8_MIDTERM_FEEDBACK_TEMPLATE"],
}

TARGET_TEMPLATES = [
    "app/templates/performance_scorecard_detail.html",
    "app/templates/performance_v2_phase5_scorecard.html",
    "app/templates/scorecard.html",
    "app/templates/performance/president_approval_scorecard.html",
    "app/templates/performance/president_approval_scorecard_v2.html",
    "app/templates/performance/president_card_review.html",
    "app/templates/performance_tasks.html",
    "app/templates/performance/evaluation_form.html",
    "app/templates/evaluation_form.html",
    "app/templates/performance/midterm_notes.html",
    "app/templates/performance/interim_feedback.html",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def load_center(root: Path):
    path = root / "app/services/performance/phase8_midterm_feedback_center.py"
    spec = importlib.util.spec_from_file_location("phase8_midterm_feedback_center_check", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def smoke_policy(root: Path) -> dict:
    center = load_center(root)
    valid = center.validate_phase8_midterm_note({"employee_id": 7, "period_id": 2026, "note_type": "achievement", "note_text": "Önemli görev zamanında tamamlandı.", "event_date": "2026-03-10"})
    invalid = center.validate_phase8_midterm_note({"employee_id": None, "period_id": None, "note_type": "achievement", "note_text": ""})
    reminder = center.build_phase8_evaluator_reminders([valid.normalized])
    scorecard = center.build_phase8_scorecard_summary([{**valid.normalized, "include_in_scorecard": True}])
    own_unpublished = center.resolve_phase8_midterm_visibility(role="personel", current_user_id=7, employee_id=7, note_status="active")
    own_published = center.resolve_phase8_midterm_visibility(role="personel", current_user_id=7, employee_id=7, note_status="published")
    manager = center.resolve_phase8_midterm_visibility(role="koordinatör", current_user_id=1, employee_id=7, same_scope=True)
    admin_publish = center.resolve_phase8_midterm_visibility(role="admin", action="publish")
    filtered = center.filter_phase8_midterm_notes([{**valid.normalized, "status": "published"}, {**valid.normalized, "employee_id": 8, "status": "active"}], current_user_id=7, role="personel")
    clean = center.phase8_clean_text("workflow state ve endpoint debug yazısı")
    contract = center.phase8_midterm_contract()
    items = {
        "version": center.BYS360_PERFORMANCE_COMPLETION_PHASE8_VERSION == "performance-completion-phase8-midterm-feedback-center-v1",
        "valid_note": valid.ok and valid.normalized["auto_score_effect"] == 0,
        "invalid_note": (not invalid.ok) and bool(invalid.errors),
        "reminder_no_score": reminder["count"] == 1 and reminder["items"][0]["score_effect"] == 0,
        "scorecard_no_score": scorecard["auto_score_effect"] == 0 and scorecard["visible_count"] == 1,
        "own_unpublished_blocked": own_unpublished.can_view is False,
        "own_published_visible": own_published.can_view is True and own_published.show_person_detail is False,
        "manager_scope": manager.can_view is True and manager.can_remind_evaluator is True,
        "admin_publish": admin_publish.can_publish is True,
        "filtered_published_only": len(filtered) == 1 and filtered[0]["employee_id"] == 7,
        "technical_clean": not center.phase8_contains_technical_language(clean),
        "contract": bool(contract.get("markers", {}).get("no_auto_score")),
    }
    return {"ok": all(items.values()), "items": items, "valid": valid.as_dict(), "reminder": reminder, "scorecard": scorecard, "contract": contract}


def app_check(root: Path) -> dict:
    code = """
from app import create_app
app = create_app()
with app.app_context():
    from app.services.performance.phase8_midterm_feedback_center import seed_phase8_midterm_feedback_settings
    import json
    print(json.dumps(seed_phase8_midterm_feedback_settings(), ensure_ascii=False))
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
        "app/services/performance/phase8_midterm_feedback_center.py",
        "app/services/performance/midterm_feedback_service.py",
        "app/services/performance/interim_feedback_policy.py",
        "app/services/performance/scorecard_midterm_notes.py",
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
        bound = "performance/_phase8_midterm_feedback_panel.html" in text or "BYS360_PERFORMANCE_COMPLETION_PHASE8_TEMPLATE_BOUND" in text
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
    print("BYS360_PERFORMANCE_COMPLETION_PHASE8_MIDTERM_FEEDBACK_CENTER_CHECK_OK" if result["ok"] else "BYS360_PERFORMANCE_COMPLETION_PHASE8_MIDTERM_FEEDBACK_CENTER_CHECK_FAIL")
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
