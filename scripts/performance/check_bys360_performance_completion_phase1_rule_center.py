# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import py_compile
import sys
from datetime import datetime
from pathlib import Path

REQUIRED_FILES = [
    "app/services/performance/phase1_rule_center.py",
    "app/performance/services/performance_rule_engine.py",
    "app/services/performance/v2_1_rule_engine.py",
    "app/services/performance/v2_1_quality_gate.py",
    "app/services/performance/publish_preflight_rules.py",
    "tests/performance/test_performance_completion_phase1_rule_center.py",
]

MARKERS = {
    "app/performance/services/performance_rule_engine.py": "BYS360_PERFORMANCE_COMPLETION_PHASE1_RULE_CENTER_DELEGATION",
    "app/services/performance/v2_1_rule_engine.py": "BYS360_PERFORMANCE_COMPLETION_PHASE1_V211_DELEGATION",
    "app/services/performance/publish_preflight_rules.py": "BYS360_PERFORMANCE_COMPLETION_PHASE1_PREFLIGHT_CENTER_MARKER",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def compile_required(root: Path) -> dict:
    errors = []
    for rel in REQUIRED_FILES:
        path = root / rel
        if path.suffix != ".py":
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            errors.append({"file": rel, "error": str(exc)})
    return {"ok": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--app-check", action="store_true", help="Flask app bağlamında kalite kapısını da çalıştırır")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    result = {
        "package": "performance_completion_phase1_rule_center",
        "version": "V1",
        "project_root": str(root),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    missing = [rel for rel in REQUIRED_FILES if not (root / rel).exists()]
    result["required_files"] = {"ok": not missing, "missing": missing}

    marker_results = []
    for rel, marker in MARKERS.items():
        ok = (root / rel).exists() and marker in read_text(root / rel)
        marker_results.append({"file": rel, "marker": marker, "ok": ok})
    result["markers"] = {"ok": all(item["ok"] for item in marker_results), "items": marker_results}

    result["compile"] = compile_required(root)

    sys.path.insert(0, str(root))
    try:
        # Flask kurulu olmayan analiz ortamlarında app paketini import etmeden dosyayı
        # doğrudan yükler. Canlı/yerel venv içinde app-check ayrıca çalıştırılabilir.
        import importlib.util

        phase1_path = root / "app" / "services" / "performance" / "phase1_rule_center.py"
        spec = importlib.util.spec_from_file_location("bys360_phase1_rule_center_direct", phase1_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("phase1_rule_center dosyası yüklenemedi")
        phase1 = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = phase1
        spec.loader.exec_module(phase1)

        decision = phase1.evaluate_phase1_rules({
            "criteria_score": 1,
            "final_score": 66,
            "status_code": "president_pending",
            "president_approved": False,
            "reviewer_level": 3,
            "third_reviewer_mode": "comment_only",
        })
        smoke = {
            "score_1_comment": phase1.is_score_comment_required(1) is True,
            "low_score_president": phase1.requires_president_approval(66) is True,
            "low_score_publish_lock": phase1.is_publish_locked(66, president_approved=False) is True,
            "status_tr": phase1.display_status("president_pending") == "Başkan Onayı Bekliyor",
            "unknown_status_safe": phase1.display_status("unknown_developer_status") == "Süreç Durumu Belirleniyor",
            "third_reviewer_comment": phase1.reviewer_action_decision(3, "comment_only").get("affects_score") is False,
            "combined_decision": bool(decision.requires_score_comment and decision.requires_general_comment and decision.requires_president_approval and decision.publish_locked),
        }
        result["phase1_smoke"] = {"ok": all(smoke.values()), "items": smoke}
    except Exception as exc:
        result["phase1_smoke"] = {"ok": False, "error": str(exc)}

    if args.app_check:
        try:
            from app import create_app
            from app.services.performance.v2_1_quality_gate import run_v2_1_1_quality_gate

            app = create_app()
            with app.app_context():
                result["app_quality_gate"] = run_v2_1_1_quality_gate()
        except Exception as exc:
            result["app_quality_gate"] = {"ok": False, "error": str(exc)}
    else:
        result["app_quality_gate"] = {"ok": True, "skipped": True}

    result["ok"] = all([
        result["required_files"].get("ok"),
        result["markers"].get("ok"),
        result["compile"].get("ok"),
        result["phase1_smoke"].get("ok"),
        result["app_quality_gate"].get("ok"),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["ok"]:
        print("BYS360_PERFORMANCE_COMPLETION_PHASE1_RULE_CENTER_OK")
        return 0
    print("BYS360_PERFORMANCE_COMPLETION_PHASE1_RULE_CENTER_FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
