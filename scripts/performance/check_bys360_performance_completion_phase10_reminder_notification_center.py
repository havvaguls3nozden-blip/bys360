# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, importlib.util, json, py_compile, sys
from datetime import date
from pathlib import Path

REQUIRED_FILES = [
    "app/services/performance/phase10_reminder_notification_center.py",
    "app/services/performance/reminder_notification_service.py",
    "app/services/performance/delayed_evaluator_service.py",
    "app/templates/performance/_phase10_reminder_notification_panel.html",
    "app/static/css/performance_completion_phase10_reminder.css",
    "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE10_REMINDER_NOTIFICATION_CENTER.md",
]

MARKERS = {
    "app/services/performance/phase10_reminder_notification_center.py": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE10_REMINDER_NOTIFICATION_CENTER",
        "BYS360_PERFORMANCE_COMPLETION_PHASE10_WEEKDAY_ONLY",
        "BYS360_PERFORMANCE_COMPLETION_PHASE10_DELAYED_EVALUATOR_REPORT",
        "BYS360_PERFORMANCE_COMPLETION_PHASE10_MAIL_LOG_REQUIRED",
        "BYS360_PERFORMANCE_COMPLETION_PHASE10_NO_ADMIN_DECISION",
        "Hafta Sonu Kuralı Nedeniyle Gönderilmedi",
    ],
    "app/templates/performance/_phase10_reminder_notification_panel.html": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE10_REMINDER_NOTIFICATION_PANEL",
        "Aksatan Amir Takibi",
    ],
    "app/static/css/performance_completion_phase10_reminder.css": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE10_REMINDER_CSS",
    ],
}


def load_center(root: Path):
    path = root / "app/services/performance/phase10_reminder_notification_center.py"
    spec = importlib.util.spec_from_file_location("phase10_center_check", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def smoke_policy(root: Path) -> dict:
    center = load_center(root)
    weekend_decision = center.phase10_reminder_decision({"reminder_type": "due_today", "due_date": "2026-06-07", "channel": "mail"}, today=date(2026, 6, 7))
    weekday_decision = center.phase10_reminder_decision({"reminder_type": "due_today", "due_date": "2026-06-08", "channel": "mail"}, today=date(2026, 6, 8))
    summary = center.phase10_delayed_evaluator_summary([
        {"evaluator_id": 1, "evaluator_name": "Amir A", "due_date": "2026-06-01", "status": "pending"},
        {"evaluator_id": 1, "evaluator_name": "Amir A", "due_date": "2026-06-08", "status": "pending"},
        {"evaluator_id": 2, "evaluator_name": "Amir B", "due_date": "2026-06-11", "status": "pending"},
    ], today=date(2026, 6, 8))
    cleaned = center.phase10_clean_text("workflow endpoint debug raw json")
    validation = center.validate_phase10_reminder({"reminder_type": "overdue", "subject": "Görev", "message": "Tamamlanmamış görev", "channel": "notification"})
    contract = center.phase10_contract()
    items = {
        "version_flag": (getattr(center, "BYS360_PERFORMANCE_COMPLETION_PHASE10_VERSION", "").endswith("v1") or getattr(center, "BYS360_PERFORMANCE_COMPLETION_PHASE10_VERSION", "").endswith("v1a")),
        "weekend_skip": weekend_decision.status == "skipped_weekend" and weekend_decision.should_send is False,
        "weekday_ready": weekday_decision.should_send is True and weekday_decision.status == "ready",
        "delayed_summary": len(summary) == 2 and summary[0]["overdue_count"] >= 1,
        "clean_text": not center.phase10_contains_technical_language(cleaned),
        "validation_ok": validation.ok,
        "contract_settings": len(contract.get("settings", [])) >= 8,
        "no_admin_decision": contract.get("markers", {}).get("no_admin_decision") is True,
        "mail_log_required": contract.get("markers", {}).get("mail_log_required") is True,
    }
    return {"ok": all(items.values()), "items": items, "weekend_decision": weekend_decision.as_dict(), "weekday_decision": weekday_decision.as_dict(), "summary": summary, "contract": contract}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    result = {"package": "performance_completion_phase10_reminder_notification_center", "version": "V1", "project_root": str(root)}
    missing = [rel for rel in REQUIRED_FILES if not (root / rel).exists()]
    result["required_files"] = {"ok": not missing, "missing": missing}
    marker_items = []
    for rel, markers in MARKERS.items():
        path = root / rel
        text = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        marker_items.append({"file": rel, "ok": all(m in text for m in markers), "markers": {m: (m in text) for m in markers}})
    result["markers"] = {"ok": all(i["ok"] for i in marker_items), "items": marker_items}
    compile_errors = []
    for rel in ["app/services/performance/phase10_reminder_notification_center.py", "app/services/performance/reminder_notification_service.py", "app/services/performance/delayed_evaluator_service.py"]:
        try:
            py_compile.compile(str(root / rel), doraise=True)
        except Exception as exc:
            compile_errors.append({"file": rel, "error": str(exc)})
    result["compile"] = {"ok": not compile_errors, "errors": compile_errors}
    result["policy_smoke"] = smoke_policy(root) if result["compile"]["ok"] and not missing else {"ok": False, "reason": "compile_or_files_failed"}
    result["ok"] = result["required_files"]["ok"] and result["markers"]["ok"] and result["compile"]["ok"] and result["policy_smoke"]["ok"]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["ok"]:
        print("BYS360_PERFORMANCE_COMPLETION_PHASE10_REMINDER_NOTIFICATION_CENTER_APPLY_OK")
        return 0
    print("BYS360_PERFORMANCE_COMPLETION_PHASE10_REMINDER_NOTIFICATION_CENTER_APPLY_FAIL")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
