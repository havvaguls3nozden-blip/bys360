# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, importlib.util, json, py_compile, subprocess, sys
from datetime import datetime
from pathlib import Path

PACKAGE = "performance_completion_phase12_final_gate"
VERSION = "V1"

REQUIRED_FILES = [
    "app/services/performance/phase12_performance_final_gate_center.py",
    "app/services/performance/performance_completion_final_gate.py",
    "app/templates/performance/_phase12_final_gate_panel.html",
    "app/static/css/performance_completion_phase12_final_gate.css",
    "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_GATE.md",
]

PY_FILES = [
    "app/services/performance/phase12_performance_final_gate_center.py",
    "app/services/performance/performance_completion_final_gate.py",
]


def load_center(root: Path):
    path = root / "app/services/performance/phase12_performance_final_gate_center.py"
    spec = importlib.util.spec_from_file_location("phase12_performance_final_gate_center_check", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Faz 12 final gate merkezi yüklenemedi")
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


def required_files_check(root: Path) -> dict:
    missing = [rel for rel in REQUIRED_FILES if not (root / rel).exists()]
    return {"ok": not missing, "missing": missing}


def markers_check(root: Path) -> dict:
    required = {
        "app/services/performance/phase12_performance_final_gate_center.py": [
            "BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_GATE",
            "BYS360_PERFORMANCE_COMPLETION_PHASE12_ALL_PHASE_GATE",
            "BYS360_PERFORMANCE_COMPLETION_PHASE12_DEVIR_READY_REPORT",
            "phase12_build_report",
            "seed_phase12_final_gate_settings",
        ],
        "app/services/performance/performance_completion_final_gate.py": [
            "BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_GATE_BRIDGE",
        ],
        "app/templates/performance/_phase12_final_gate_panel.html": [
            "BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_GATE_PANEL",
            "Performans Modülü Final Gate",
        ],
        "app/static/css/performance_completion_phase12_final_gate.css": [
            "BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_GATE_CSS",
        ],
    }
    items = []
    for rel, markers in required.items():
        path = root / rel
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        marker_result = {marker: marker in text for marker in markers}
        items.append({"file": rel, "ok": all(marker_result.values()), "markers": marker_result})
    return {"ok": all(item["ok"] for item in items), "items": items}


def smoke_policy(root: Path) -> dict:
    center = load_center(root)
    statuses = []
    for phase in center.PHASE12_PHASES:
        statuses.append(center.phase12_basic_phase_status(root, phase, check_ok=True))
    report = center.phase12_build_report(root, statuses)
    md = center.phase12_generate_markdown_report(report)
    items = {
        "version_flag": getattr(center, "BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_GATE", False) is True,
        "phase_count": report.get("phase_count") == 11,
        "score_100_when_all_ok": report.get("completion_score") == 100.0,
        "final_label": "100" in report.get("status_label", "") or "Kapanışa Hazır" in report.get("status_label", ""),
        "no_new_score": getattr(center, "BYS360_PERFORMANCE_COMPLETION_PHASE12_NO_NEW_SCORE", False) is True,
        "no_admin_decision": getattr(center, "BYS360_PERFORMANCE_COMPLETION_PHASE12_NO_ADMIN_DECISION", False) is True,
        "markdown": "Faz Kontrol Özeti" in md and "puan" in md.lower(),
        "settings_catalog": len(center.PHASE12_SETTING_ROWS) >= 5,
    }
    return {"ok": all(items.values()), "items": items, "sample_report": {"completion_score": report.get("completion_score"), "status_label": report.get("status_label")}}


def run_subcheck(root: Path, script_rel: str, timeout: int = 180) -> dict:
    path = root / script_rel
    if not path.exists():
        return {"ok": False, "missing": True, "script": script_rel}
    try:
        proc = subprocess.run([sys.executable, str(path), "--project-root", str(root)], cwd=str(root), text=True, capture_output=True, timeout=timeout)
        stdout_tail = "\n".join((proc.stdout or "").splitlines()[-20:])
        stderr_tail = "\n".join((proc.stderr or "").splitlines()[-20:])
        return {"ok": proc.returncode == 0, "script": script_rel, "exit_code": proc.returncode, "stdout_tail": stdout_tail, "stderr_tail": stderr_tail}
    except subprocess.TimeoutExpired as exc:
        return {"ok": False, "script": script_rel, "timeout": True, "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "script": script_rel, "error": str(exc)}


def all_phase_gate(root: Path, run_subchecks: bool) -> dict:
    center = load_center(root)
    phase_statuses = []
    subchecks = []
    for phase in center.PHASE12_PHASES:
        sub_ok = None
        if run_subchecks:
            sub = run_subcheck(root, phase["check_script"])
            subchecks.append(sub)
            sub_ok = bool(sub.get("ok"))
        phase_statuses.append(center.phase12_basic_phase_status(root, phase, check_ok=sub_ok).as_dict())
    score = center.phase12_completion_score(phase_statuses)
    report = center.phase12_build_report(root, [center.phase12_basic_phase_status(root, phase, check_ok=(subchecks[idx].get("ok") if run_subchecks else None)) for idx, phase in enumerate(center.PHASE12_PHASES)])
    return {"ok": report.get("ok"), "completion_score": score, "status_label": report.get("status_label"), "phases": phase_statuses, "subchecks": subchecks, "report": report}


def app_check(root: Path) -> dict:
    code = """
from app import create_app
app = create_app()
with app.app_context():
    from app.services.performance.phase12_performance_final_gate_center import phase12_contract
    import json
    print(json.dumps({"ok": True, "contract": phase12_contract()}, ensure_ascii=False))
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
    parser.add_argument("--run-subchecks", action="store_true", help="Faz 1-11 check scriptlerini de çalıştırır")
    parser.add_argument("--skip-app-check", action="store_true")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    result = {"package": PACKAGE, "version": VERSION, "project_root": str(root), "generated_at": datetime.now().isoformat(timespec="seconds")}
    result["required_files"] = required_files_check(root)
    result["markers"] = markers_check(root)
    result["compile"] = compile_files(root)
    result["policy_smoke"] = smoke_policy(root)
    result["all_phase_gate"] = all_phase_gate(root, run_subchecks=args.run_subchecks)
    if not args.skip_app_check:
        result["app_check"] = app_check(root)
    else:
        result["app_check"] = {"ok": True, "skipped": True}
    result["ok"] = all([
        result["required_files"].get("ok"),
        result["markers"].get("ok"),
        result["compile"].get("ok"),
        result["policy_smoke"].get("ok"),
        result["all_phase_gate"].get("ok"),
        result["app_check"].get("ok"),
    ])
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    if result["ok"]:
        print("BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_GATE_CHECK_OK")
    else:
        print("BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_GATE_CHECK_FAIL")
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
