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
    "app/services/performance/completion_phase4_third_manager_center.py",
    "app/services/performance/phase4_third_manager_policy.py",
    "app/services/performance/third_supervisor_policy.py",
    "app/services/performance/third_supervisor_column_visibility.py",
    "app/services/performance/assignment_builder.py",
]

COMPILE_FILES = REQUIRED_FILES + [
    "app/services/performance/chain_rule_engine.py",
    "app/services/performance/manager_rule_constitution.py",
]

MARKERS = {
    "app/services/performance/completion_phase4_third_manager_center.py": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE4_THIRD_MANAGER_CENTER",
        "BYS360_PERFORMANCE_COMPLETION_PHASE4_NO_FAKE_THIRD_TASK",
        "BYS360_PERFORMANCE_COMPLETION_PHASE4_COMMENT_SCORE_MODE_SPLIT",
        "BYS360_PERFORMANCE_COMPLETION_PHASE4_WEIGHT_TOTAL_100",
        "3. Amir Görüş/Yorum Bekliyor",
        "3. Amir Puanlama Bekliyor",
    ],
    "app/services/performance/phase4_third_manager_policy.py": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE4_POLICY_WRAPPER",
        "resolve_phase4_third_manager_decision",
    ],
    "app/services/performance/third_supervisor_policy.py": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE4_THIRD_SUPERVISOR_POLICY_BRIDGE",
        "phase4_should_create_third_manager_task",
        "phase4_humanize_assignment_status",
    ],
    "app/services/performance/third_supervisor_column_visibility.py": [
        "BYS360_PERFORMANCE_COMPLETION_PHASE4_THIRD_COLUMN_BRIDGE",
        "phase4_should_show_third_manager_column",
    ],
    "app/services/performance/assignment_builder.py": [
        "should_create_third_supervisor_task",
    ],
}


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


class DummyAssignment:
    manager_level = 3
    status = "bekliyor"
    completed_at = None
    evaluator_id = 44


def phase4_smoke(root: Path) -> dict[str, Any]:
    try:
        module = load_module_from_file(
            root,
            "app/services/performance/completion_phase4_third_manager_center.py",
            "bys360_phase4_third_manager_center_direct",
        )
        comment_settings = {"third_supervisor_enabled": "true", "third_supervisor_mode": "comment_only", "third_supervisor_weight_enabled": "false"}
        score_settings = {"third_supervisor_enabled": "true", "third_supervisor_mode": "scoring", "third_supervisor_weight_enabled": "true"}
        off_settings = {"third_supervisor_enabled": "false", "third_supervisor_mode": "off"}

        missing = module.resolve_phase4_third_manager_decision(settings=comment_settings)
        comment = module.resolve_phase4_third_manager_decision(third_manager_id=44, settings=comment_settings)
        scoring = module.resolve_phase4_third_manager_decision(third_manager_id=44, settings=score_settings)
        disabled = module.resolve_phase4_third_manager_decision(third_manager_id=44, settings=off_settings)
        filtered = module.phase4_filter_third_manager_tasks([
            {"manager_level": 3, "evaluator_id": None, "status": "bekliyor"},
            {"manager_level": 3, "evaluator_id": 44, "status": "bekliyor"},
            {"manager_level": 2, "evaluator_id": 12, "status": "bekliyor"},
        ], settings=comment_settings)
        comment_weights = module.normalize_phase4_manager_weights(
            {"evaluator_1_weight": 60, "evaluator_2_weight": 40, "evaluator_3_weight": 20},
            manager_1_id=1,
            manager_2_id=2,
            manager_3_id=44,
            settings=comment_settings,
        )
        score_weights = module.normalize_phase4_manager_weights(
            {"evaluator_1_weight": 40, "evaluator_2_weight": 40, "evaluator_3_weight": 20},
            manager_1_id=1,
            manager_2_id=2,
            manager_3_id=44,
            settings=score_settings,
        )
        contract = module.phase4_static_contract()
        smoke = {
            "version_flag": getattr(module, "BYS360_PERFORMANCE_COMPLETION_PHASE4_THIRD_MANAGER_CENTER", False) is True,
            "missing_no_column": missing.show_column is False and missing.create_task is False,
            "comment_has_task": comment.create_task is True,
            "comment_no_score": comment.score_required is False and comment.comment_required is True and comment.include_weight is False,
            "comment_language": "Görüş/Yorum" in comment.status_label and "Puanlama" not in comment.status_label,
            "score_mode": scoring.score_required is True and scoring.include_weight is True and "Puanlama" in scoring.status_label,
            "disabled_mode": disabled.create_task is False and disabled.show_column is False,
            "fake_task_removed": len(filtered) == 2 and all(not (row.get("manager_level") == 3 and not row.get("evaluator_id")) for row in filtered),
            "column_data_only": module.phase4_should_show_third_manager_column([{"manager_3_id": None}], settings=comment_settings) is False,
            "column_real_third": module.phase4_should_show_third_manager_column([{"manager_3_id": 44}], settings=comment_settings) is True,
            "comment_weight_zero": round(comment_weights.get("evaluator_3_weight", -1), 2) == 0.0 and round(sum(comment_weights.values()), 2) == 100.0,
            "score_weight_total": round(sum(score_weights.values()), 2) == 100.0 and score_weights.get("evaluator_3_weight", 0) > 0,
            "humanized_comment": "Görüş/Yorum" in module.phase4_humanize_assignment_status(DummyAssignment(), status="bekliyor"),
            "settings_catalog": len(contract.get("settings") or []) >= 7,
        }
        return {"ok": all(smoke.values()), "items": smoke, "comment_weights": comment_weights, "score_weights": score_weights, "contract": contract}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def app_check(root: Path) -> dict[str, Any]:
    sys.path.insert(0, str(root))
    try:
        from app import create_app
        from app.services.performance.completion_phase4_third_manager_center import seed_phase4_third_manager_center, phase4_static_contract

        app = create_app()
        with app.app_context():
            seed_result = seed_phase4_third_manager_center(commit=True)
            contract = phase4_static_contract()
            return {
                "ok": bool(seed_result.get("ok")) and len(contract.get("settings") or []) >= 7,
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
        "package": "performance_completion_phase4_third_manager_center",
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
    result["phase4_smoke"] = phase4_smoke(root)
    result["app_check"] = app_check(root) if args.app_check else {"ok": True, "skipped": True}

    result["ok"] = all([
        result["required_files"].get("ok"),
        result["markers"].get("ok"),
        result["compile"].get("ok"),
        result["phase4_smoke"].get("ok"),
        result["app_check"].get("ok"),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["ok"]:
        print("BYS360_PERFORMANCE_COMPLETION_PHASE4_THIRD_MANAGER_CENTER_OK")
        return 0
    print("BYS360_PERFORMANCE_COMPLETION_PHASE4_THIRD_MANAGER_CENTER_FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
