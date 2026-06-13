# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, importlib.util, json, py_compile, subprocess, sys
from datetime import datetime
from pathlib import Path

PACKAGE = "performance_completion_phase9_development_guidance_center"
VERSION = "V1"

REQUIRED_FILES = [
    "app/services/performance/phase9_development_guidance_center.py",
    "app/services/performance/development_guidance_service.py",
    "app/services/performance/scorecard_development_guidance.py",
    "app/services/performance/evaluator_development_guidance.py",
    "app/templates/performance/_phase9_development_guidance_panel.html",
    "app/static/css/performance_completion_phase9_development_guidance.css",
    "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_CENTER.md",
]

MARKERS = {
    "app/services/performance/phase9_development_guidance_center.py": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_CENTER",
        "BYS360_PERFORMANCE_COMPLETION_PHASE9_NO_AUTO_SCORE",
        "BYS360_PERFORMANCE_COMPLETION_PHASE9_NO_ADMIN_DECISION",
        "BYS360_PERFORMANCE_COMPLETION_PHASE9_SCORECARD_GUIDANCE",
        "validate_phase9_guidance",
        "resolve_phase9_guidance_visibility",
        "build_phase9_scorecard_guidance_summary",
        "build_phase9_evaluator_guidance_context",
    ],
    "app/services/performance/development_guidance_service.py": ["BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_SERVICE_BRIDGE"],
    "app/services/performance/scorecard_development_guidance.py": ["BYS360_PERFORMANCE_COMPLETION_PHASE9_SCORECARD_GUIDANCE_BRIDGE"],
    "app/services/performance/evaluator_development_guidance.py": ["BYS360_PERFORMANCE_COMPLETION_PHASE9_EVALUATOR_GUIDANCE_BRIDGE"],
    "app/templates/performance/_phase9_development_guidance_panel.html": ["BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_TEMPLATE"],
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
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def load_center(root: Path):
    path = root / "app/services/performance/phase9_development_guidance_center.py"
    spec = importlib.util.spec_from_file_location("phase9_development_guidance_center_check", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def smoke_policy(root: Path) -> dict:
    center = load_center(root)
    valid = center.validate_phase9_guidance({
        "employee_id": 7,
        "period_id": 2026,
        "guidance_type": "development_need",
        "guidance_text": "Raporlama takibinin dönem içinde daha düzenli yapılması önerilir.",
        "source": "scorecard",
        "priority": "high",
        "suggested_action": "Aylık kısa takip görüşmesi yapılabilir.",
        "include_in_scorecard": True,
    })
    invalid = center.validate_phase9_guidance({"employee_id": None, "guidance_type": "development_need", "guidance_text": "", "source": "scorecard"})
    scorecard = center.build_phase9_scorecard_guidance_summary([valid.normalized])
    evaluator = center.build_phase9_evaluator_guidance_context([valid.normalized])
    own_unpublished = center.resolve_phase9_guidance_visibility(role="personel", current_user_id=7, employee_id=7, guidance_status="active")
    own_published = center.resolve_phase9_guidance_visibility(role="personel", current_user_id=7, employee_id=7, guidance_status="published")
    manager = center.resolve_phase9_guidance_visibility(role="koordinatör", current_user_id=1, employee_id=7, same_scope=True)
    admin_publish = center.resolve_phase9_guidance_visibility(role="admin", action="publish")
    filtered = center.filter_phase9_guidance_items([{**valid.normalized, "status": "published", "employee_visible": True}, {**valid.normalized, "employee_id": 8, "status": "active"}], current_user_id=7, role="personel")
    clean = center.phase9_clean_text("workflow state ve endpoint debug yazısı")
    contract = center.phase9_guidance_contract()
    items = {
        "version": center.BYS360_PERFORMANCE_COMPLETION_PHASE9_VERSION == "performance-completion-phase9-development-guidance-center-v1",
        "valid_guidance": valid.ok and valid.normalized["auto_score_effect"] == 0 and valid.normalized["admin_decision_effect"] is False,
        "invalid_guidance": (not invalid.ok) and bool(invalid.errors),
        "scorecard_no_score": scorecard["auto_score_effect"] == 0 and scorecard["admin_decision_effect"] is False and scorecard["visible_count"] == 1,
        "evaluator_no_score": evaluator["auto_score_effect"] == 0 and evaluator["admin_decision_effect"] is False and evaluator["count"] == 1,
        "own_unpublished_blocked": own_unpublished.can_view is False,
        "own_published_visible": own_published.can_view is True and own_published.show_person_detail is False,
        "manager_scope": manager.can_view is True and manager.can_follow_up is True,
        "admin_publish": admin_publish.can_publish is True,
        "filtered_published_only": len(filtered) == 1 and filtered[0]["employee_id"] == 7,
        "technical_clean": not center.phase9_contains_technical_language(clean),
        "contract": bool(contract.get("markers", {}).get("no_auto_score")) and bool(contract.get("markers", {}).get("no_admin_decision")),
    }
    return {"ok": all(items.values()), "items": items, "valid": valid.as_dict(), "scorecard": scorecard, "evaluator": evaluator, "contract": contract}


def app_check(root: Path) -> dict:
    code = """
from app import create_app
app = create_app()
with app.app_context():
    from app.services.performance.phase9_development_guidance_center import seed_phase9_development_guidance_settings
    import json
    print(json.dumps(seed_phase9_development_guidance_settings(), ensure_ascii=False))
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
        "app/services/performance/phase9_development_guidance_center.py",
        "app/services/performance/development_guidance_service.py",
        "app/services/performance/scorecard_development_guidance.py",
        "app/services/performance/evaluator_development_guidance.py",
        "scripts/performance/check_bys360_performance_completion_phase9_development_guidance_center.py",
        "scripts/performance/repair_bys360_performance_completion_phase9_development_guidance_center.py",
    ]:
        path = root / rel
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                result["compile"]["ok"] = False
                result["compile"]["errors"].append({"file": rel, "error": str(exc)})
    for rel in TARGET_TEMPLATES:
        path = root / rel
        if path.exists():
            text = read(path)
            ok = "BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_INCLUDE" in text
            result["templates"]["items"].append({"file": rel, "patched": ok})
    result["templates"]["ok"] = any(item.get("patched") for item in result["templates"]["items"]) if result["templates"]["items"] else True
    result["policy_smoke"] = smoke_policy(root)
    result["app_check"] = app_check(root)
    result["ok"] = all([
        result["required_files"]["ok"],
        result["markers"]["ok"],
        result["compile"]["ok"],
        result["templates"]["ok"],
        result["policy_smoke"].get("ok"),
        result["app_check"].get("ok"),
    ])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["ok"]:
        print("BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_CENTER_APPLY_OK")
        return 0
    print("BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_CENTER_FAIL")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
