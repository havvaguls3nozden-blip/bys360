# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, subprocess, sys, py_compile
from datetime import datetime
from pathlib import Path

PACKAGE = "performance_completion_phase9_development_guidance_center"
VERSION = "V1_SAFE_REPAIR"

SERVICE_FILES = [
    "app/services/performance/phase9_development_guidance_center.py",
    "app/services/performance/development_guidance_service.py",
    "app/services/performance/scorecard_development_guidance.py",
    "app/services/performance/evaluator_development_guidance.py",
]

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

INCLUDE_SNIPPET = """{# BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_INCLUDE #}
{% include 'performance/_phase9_development_guidance_panel.html' ignore missing %}"""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def repair_literal_backslash_newlines(root: Path) -> dict:
    changed = []
    for rel in SERVICE_FILES:
        path = root / rel
        if not path.exists():
            continue
        text = read_text(path)
        # Previous V1 repair accidentally wrote literal \n sequences into the Python file.
        if text.startswith("\\n#") or text.startswith("\\n# -*-") or "\\nfrom __future__" in text[:400]:
            try:
                repaired = text.encode("utf-8").decode("unicode_escape")
            except Exception:
                repaired = text.replace("\\n", "\n").replace("\\t", "\t")
            if repaired.startswith("\n"):
                repaired = repaired.lstrip("\n")
            write_text(path, repaired)
            changed.append(rel)
    return {"ok": True, "changed": changed}


def patch_templates(root: Path) -> dict:
    changed = []
    for rel in TARGET_TEMPLATES:
        path = root / rel
        if not path.exists():
            continue
        text = read_text(path)
        if "BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_INCLUDE" in text:
            continue
        if "{% endblock" in text:
            idx = text.rfind("{% endblock")
            text = text[:idx].rstrip() + "\n\n" + INCLUDE_SNIPPET + "\n" + text[idx:]
        else:
            text = text.rstrip() + "\n\n" + INCLUDE_SNIPPET + "\n"
        write_text(path, text)
        changed.append(rel)
    return {"ok": True, "changed": changed}


def compile_files(root: Path) -> dict:
    errors = []
    for rel in SERVICE_FILES + [
        "scripts/performance/check_bys360_performance_completion_phase9_development_guidance_center.py",
        "scripts/performance/repair_bys360_performance_completion_phase9_development_guidance_center.py",
    ]:
        path = root / rel
        if not path.exists():
            errors.append({"file": rel, "error": "missing"})
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            errors.append({"file": rel, "error": str(exc)})
    return {"ok": not errors, "errors": errors}


def seed_settings(root: Path) -> dict:
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


def run_check(root: Path) -> dict:
    script = root / "scripts/performance/check_bys360_performance_completion_phase9_development_guidance_center.py"
    proc = subprocess.run([sys.executable, str(script), "--project-root", str(root)], cwd=str(root), text=True, capture_output=True)
    return {"exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "ok": proc.returncode == 0}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="all", choices=["patch", "seed", "check", "all"])
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    result = {
        "package": PACKAGE,
        "version": VERSION,
        "project_root": str(root),
        "mode": args.mode,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "literal_newline_repair": None,
        "template_patch": None,
        "compile": None,
        "seed": None,
        "check": None,
        "ok": False,
    }
    if args.mode in {"patch", "all"}:
        result["literal_newline_repair"] = repair_literal_backslash_newlines(root)
        result["template_patch"] = patch_templates(root)
        result["compile"] = compile_files(root)
    if args.mode in {"seed", "all"}:
        result["seed"] = seed_settings(root)
    if args.mode in {"check", "all"}:
        result["check"] = run_check(root)
    checks = []
    for key in ["literal_newline_repair", "template_patch", "compile", "seed", "check"]:
        if result.get(key) is not None:
            checks.append(bool(result[key].get("ok")))
    result["ok"] = all(checks) if checks else True
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["ok"]:
        print("BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_CENTER_APPLY_OK")
        return 0
    print("BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_CENTER_APPLY_FAIL")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
