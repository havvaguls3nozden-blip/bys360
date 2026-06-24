# -*- coding: utf-8 -*-
"""BYS360 P6B Android responsive visual regression evidence suite gate.

This gate is intentionally evidence-oriented. It does not require screenshots yet;
it verifies that P5F/P6A evidence is present, creates the regression evidence
folders, counts optional screenshots/findings, and produces a handover-ready
report for CI/devir teslim.
"""
from __future__ import annotations

import argparse
import json
import os
import py_compile
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P6B_ANDROID_RESPONSIVE_VISUAL_REGRESSION_EVIDENCE_SUITE_GATE"
REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_VISUAL_REGRESSION_EVIDENCE_SUITE_GATE_P6B_REPORT.json")
P6A_REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_VISUAL_REGRESSION_GATE_P6A_REPORT.json")
P5F_REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_FINAL_EVIDENCE_GATE_P5F_REPORT.json")
P6A_GUIDE_REL = Path("docs/qa/BYS360_ANDROID_RESPONSIVE_VISUAL_REGRESSION_GUIDE_P6A.md")
P6A_FINDINGS_TEMPLATE_REL = Path("docs/qa/BYS360_ANDROID_RESPONSIVE_UAT_FINDINGS_TEMPLATE_P6A.md")
P6B_EVIDENCE_DOC_REL = Path("docs/qa/BYS360_ANDROID_RESPONSIVE_VISUAL_REGRESSION_EVIDENCE_SUITE_P6B.md")
P6B_INDEX_REL = Path("reports/visual/android_responsive_p6b/BYS360_ANDROID_RESPONSIVE_VISUAL_REGRESSION_FINDINGS_INDEX_P6B.md")

EXPECTED_ROUTE_COUNT = 24
SCREENSHOT_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
FINDING_EXTS = {".md", ".json", ".txt"}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig", errors="replace")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "missing_report", "path": str(path)}
    try:
        return json.loads(_read_text(path))
    except Exception as exc:  # pragma: no cover - defensive report parser
        return {"exists": True, "ok": False, "error": f"json_parse_error: {exc}", "path": str(path)}


def _python_executable(root: Path) -> str:
    win_python = root / ".venv" / "Scripts" / "python.exe"
    posix_python = root / ".venv" / "bin" / "python"
    if win_python.exists():
        return str(win_python)
    if posix_python.exists():
        return str(posix_python)
    return sys.executable


def _route_count_in_file(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    text = _read_text(path)
    # Count Flask blueprint/app route decorators. This intentionally stays broad
    # because the mobile domain modules use multiple blueprint naming styles.
    return len(re.findall(r"^\s*@[^\n]*\.route\s*\(", text, flags=re.MULTILINE))


def _route_inventory(root: Path) -> Dict[str, Any]:
    mobile_dir = root / "app" / "api" / "mobile"
    routes_py = mobile_dir / "routes.py"
    domain_dir = mobile_dir / "domains"
    files: List[Path] = []
    if routes_py.exists():
        files.append(routes_py)
    if domain_dir.exists():
        files.extend(sorted(domain_dir.glob("*.py")))

    domain_inventory: List[Dict[str, Any]] = []
    total = 0
    for path in files:
        count = _route_count_in_file(path)
        total += count
        try:
            lines = len(_read_text(path).splitlines())
        except Exception:
            lines = None
        domain_inventory.append({
            "path": str(path.relative_to(root)).replace("\\", "/"),
            "exists": path.exists(),
            "route_count": count,
            "lines": lines,
        })

    routes_lines = len(_read_text(routes_py).splitlines()) if routes_py.exists() else None
    return {
        "routes_py_lines": routes_lines,
        "routes_py_under_300_lines": bool(routes_lines is not None and routes_lines <= 300),
        "routes_py_route_count": _route_count_in_file(routes_py),
        "domains_dir_exists": domain_dir.exists(),
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": total,
        "expected_contract_route_count": EXPECTED_ROUTE_COUNT,
        "route_contract_count_expected": total == EXPECTED_ROUTE_COUNT,
    }


def _compile_files(root: Path, rels: Iterable[Path]) -> Tuple[bool, List[Dict[str, str]]]:
    results: List[Dict[str, str]] = []
    for rel in rels:
        path = root / rel
        if not path.exists():
            results.append({"file": str(path), "ok": False, "error": "missing"})
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            results.append({"file": str(path), "ok": True, "error": ""})
        except Exception as exc:
            results.append({"file": str(path), "ok": False, "error": str(exc)})
    return all(item["ok"] for item in results), results


def _run_cmd(cmd: List[str], cwd: Path, env: Dict[str, str] | None = None) -> Dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, text=True, capture_output=True)
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-1500:],
        "stderr_tail": proc.stderr[-1500:],
        "ok": proc.returncode == 0,
        "cmd": cmd,
    }


def _extract_last_json(text: str) -> Dict[str, Any]:
    # Prefer the last balanced-looking object printed by our quality scripts.
    candidates = re.findall(r"\{[\s\S]*?\}\s*$", text.strip())
    for candidate in reversed(candidates):
        try:
            return json.loads(candidate)
        except Exception:
            continue
    # Fallback: scan from every opening brace near the end.
    for idx in [m.start() for m in re.finditer(r"\{", text)][-20:][::-1]:
        try:
            return json.loads(text[idx:])
        except Exception:
            pass
    return {}


def _app_factory_smoke(root: Path, python_exe: str) -> Dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("FLASK_ENV", "testing")
    env.setdefault("BYS360_TESTING", "1")
    env.setdefault("DATABASE_URL", "sqlite:///:memory:")
    env.setdefault("SECRET_KEY", "bys360-test-secret-key")
    return _run_cmd([python_exe, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], root, env=env)


def _secret_gate(root: Path, python_exe: str) -> Dict[str, Any]:
    script = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    if not script.exists():
        return {"ok": False, "returncode": None, "error": "missing_secret_gate", "cmd": [python_exe, str(script)]}
    result = _run_cmd([python_exe, str(script), "--root", str(root)], root)
    parsed = _extract_last_json(result.get("stdout_tail", ""))
    if parsed:
        result["parsed"] = parsed
        result["ok"] = bool(parsed.get("ok")) and result["returncode"] == 0
    return result


def _pytest_gate(root: Path, python_exe: str) -> Dict[str, Any]:
    test_path = Path("tests/architecture/test_android_responsive_visual_regression_evidence_suite_p6b.py")
    result = _run_cmd([python_exe, "-m", "pytest", str(test_path), "-q"], root)
    result["mode"] = "pytest_targeted_android_responsive_visual_regression_evidence_suite_p6b"
    return result


def _list_files(paths: Iterable[Path], exts: set[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for base in paths:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix.lower() in exts:
                out.append({
                    "path": str(path),
                    "name": path.name,
                    "size_bytes": path.stat().st_size,
                })
    return out


def _ensure_visual_dirs(root: Path) -> Dict[str, Any]:
    p6a_base = root / "reports" / "visual" / "android_responsive_p6a"
    p6b_base = root / "reports" / "visual" / "android_responsive_p6b"
    dirs = {
        "p6a_screenshots": p6a_base / "screenshots",
        "p6a_findings": p6a_base / "findings",
        "p6b_screenshots": p6b_base / "screenshots",
        "p6b_findings": p6b_base / "findings",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    screenshots = _list_files([dirs["p6a_screenshots"], dirs["p6b_screenshots"]], SCREENSHOT_EXTS)
    findings = _list_files([dirs["p6a_findings"], dirs["p6b_findings"]], FINDING_EXTS)
    return {
        "dirs": {key: str(path) for key, path in dirs.items()},
        "screenshot_count": len(screenshots),
        "screenshots": screenshots,
        "finding_count": len(findings),
        "finding_files": findings,
        "screenshot_evidence_optional_ok": True,
        "findings_tracking_ok": True,
    }


def _make_docs(root: Path, p6a: Dict[str, Any], visual_dirs: Dict[str, Any]) -> Dict[str, Any]:
    p6a_visual = p6a.get("visual_regression_evidence", {}) if isinstance(p6a, dict) else {}
    device_count = p6a.get("android_device_matrix_count") or p6a_visual.get("device_count") or 0
    surface_count = p6a.get("target_surface_count") or p6a_visual.get("target_surface_count") or 0
    expected_flags = p6a_visual.get("expected_surface_flags") or [
        "dashboard", "home", "evaluation_form", "admin_ai", "wide_tables", "wide_forms", "android_small", "landscape"
    ]
    now = datetime.now().isoformat(timespec="seconds")
    doc = f"""# BYS360 Android Responsive Visual Regression Evidence Suite - P6B

Generated: {now}

## Purpose

This evidence suite links the Android responsive final evidence (P5F) and visual regression readiness (P6A) to a reusable UAT/regression tracking standard.

## Current status

- P6A report OK: {bool(p6a.get('ok'))}
- Device matrix count: {device_count}
- Target surface count: {surface_count}
- Screenshot evidence: optional
- Screenshot count: {visual_dirs.get('screenshot_count', 0)}
- Finding count: {visual_dirs.get('finding_count', 0)}

## Expected visual surfaces

{os.linesep.join(f'- {flag}' for flag in expected_flags)}

## Evidence folders

- P6A screenshots: `{visual_dirs['dirs']['p6a_screenshots']}`
- P6A findings: `{visual_dirs['dirs']['p6a_findings']}`
- P6B screenshots: `{visual_dirs['dirs']['p6b_screenshots']}`
- P6B findings: `{visual_dirs['dirs']['p6b_findings']}`

## Rule

A missing screenshot is not a failure in P6B. A screenshot or finding file, when added later, is counted automatically in the evidence report.
"""
    _write_text(root / P6B_EVIDENCE_DOC_REL, doc)

    index = f"""# BYS360 Android Responsive Visual Regression Findings Index - P6B

Generated: {now}

## Screenshot count

{visual_dirs.get('screenshot_count', 0)}

## Finding count

{visual_dirs.get('finding_count', 0)}

## Finding files

{os.linesep.join(f"- `{item['path']}`" for item in visual_dirs.get('finding_files', [])) or '- No findings recorded.'}

## Screenshot files

{os.linesep.join(f"- `{item['path']}`" for item in visual_dirs.get('screenshots', [])) or '- No screenshots recorded.'}
"""
    _write_text(root / P6B_INDEX_REL, index)

    return {
        "evidence_doc": {
            "path": str(root / P6B_EVIDENCE_DOC_REL),
            "exists": (root / P6B_EVIDENCE_DOC_REL).exists(),
            "line_count": len(_read_text(root / P6B_EVIDENCE_DOC_REL).splitlines()),
            "ok": (root / P6B_EVIDENCE_DOC_REL).exists(),
        },
        "findings_index": {
            "path": str(root / P6B_INDEX_REL),
            "exists": (root / P6B_INDEX_REL).exists(),
            "line_count": len(_read_text(root / P6B_INDEX_REL).splitlines()),
            "ok": (root / P6B_INDEX_REL).exists(),
        },
    }


def build_report(root: Path, compile_all: bool, app_factory: bool, secret_gate: bool, pytest_gate: bool) -> Dict[str, Any]:
    root = root.resolve()
    python_exe = _python_executable(root)
    p6a = _read_json(root / P6A_REPORT_REL)
    p5f = _read_json(root / P5F_REPORT_REL)
    inventory = _route_inventory(root)
    visual_dirs = _ensure_visual_dirs(root)
    docs = _make_docs(root, p6a, visual_dirs)

    p6a_report_ok = bool(p6a.get("ok") and p6a.get("android_responsive_visual_regression_gate_ok"))
    p5f_report_ok = bool(p5f.get("ok") and p5f.get("android_responsive_final_evidence_gate_ok"))
    guide_ok = (root / P6A_GUIDE_REL).exists() or bool(p6a.get("visual_regression_guide_ok"))
    template_ok = (root / P6A_FINDINGS_TEMPLATE_REL).exists() or bool(p6a.get("visual_regression_findings_template_ok"))
    p5_phase_count = int(p6a.get("p5_phase_count") or p5f.get("p5_phase_count") or 0)
    p5_phases_passed = int(p6a.get("p5_phases_passed") or p5f.get("p5_phases_passed") or 0)

    compile_ok = True
    compile_results: List[Dict[str, str]] = []
    if compile_all:
        compile_ok, compile_results = _compile_files(root, [
            Path("scripts/quality/bys360_android_responsive_visual_regression_evidence_suite_gate_p6b.py"),
            Path("tests/architecture/test_android_responsive_visual_regression_evidence_suite_p6b.py"),
            Path("tests/architecture/conftest.py"),
            Path("scripts/quality/bys360_android_responsive_visual_regression_gate_p6a.py"),
            Path("scripts/quality/bys360_android_responsive_final_evidence_gate_p5f.py"),
        ])

    app_factory_result: Dict[str, Any] = {"ok": True, "skipped": True}
    if app_factory:
        app_factory_result = _app_factory_smoke(root, python_exe)

    secret_result: Dict[str, Any] = {"ok": True, "skipped": True, "parsed": {"finding_count": 0}}
    if secret_gate:
        secret_result = _secret_gate(root, python_exe)

    pytest_result: Dict[str, Any] = {"ok": True, "skipped": True, "mode": "pytest_skipped"}
    if pytest_gate:
        pytest_result = _pytest_gate(root, python_exe)

    secret_finding_count = int(secret_result.get("parsed", {}).get("finding_count", 0) or 0)

    visual_regression_evidence_suite_ok = all([
        p6a_report_ok,
        p5f_report_ok,
        bool(p6a.get("visual_regression_ready_ok", True)),
        bool(p6a.get("final_handover_evidence_ok", True)),
        guide_ok,
        template_ok,
        docs["evidence_doc"]["ok"],
        docs["findings_index"]["ok"],
        visual_dirs["findings_tracking_ok"],
        inventory["route_contract_count_expected"],
    ])

    ok = all([
        visual_regression_evidence_suite_ok,
        compile_ok,
        bool(app_factory_result.get("ok")),
        bool(secret_result.get("ok")),
        secret_finding_count == 0,
        bool(pytest_result.get("ok")),
    ])

    report: Dict[str, Any] = {
        "ok": ok,
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "android_responsive_visual_regression_evidence_suite_gate_ok": visual_regression_evidence_suite_ok,
        "visual_regression_evidence_suite_ok": visual_regression_evidence_suite_ok,
        "p6a_visual_regression_report_ok": p6a_report_ok,
        "p5f_final_evidence_report_ok": p5f_report_ok,
        "visual_regression_ready_ok": bool(p6a.get("visual_regression_ready_ok")) if p6a else False,
        "visual_regression_guide_ok": guide_ok,
        "visual_regression_findings_template_ok": template_ok,
        "visual_regression_evidence_doc_ok": docs["evidence_doc"]["ok"],
        "findings_index_ok": docs["findings_index"]["ok"],
        "screenshot_evidence_optional_ok": True,
        "screenshot_count": visual_dirs["screenshot_count"],
        "finding_count": visual_dirs["finding_count"],
        "findings_tracking_ok": visual_dirs["findings_tracking_ok"],
        "p5_phase_count": p5_phase_count,
        "p5_phases_passed": p5_phases_passed,
        "android_device_matrix_ok": bool(p6a.get("android_device_matrix_ok") or p5f.get("android_device_matrix_ok")),
        "android_device_matrix_count": int(p6a.get("android_device_matrix_count") or p5f.get("android_device_matrix_count") or 0),
        "target_surface_inventory_ok": bool(p6a.get("target_surface_inventory_ok") or p5f.get("target_surface_inventory_ok")),
        "target_surface_count": int(p6a.get("target_surface_count") or p5f.get("target_surface_count") or 0),
        "target_surface_exists_count": int(p6a.get("target_surface_exists_count") or p5f.get("target_surface_exists_count") or 0),
        "routes_py_lines": inventory["routes_py_lines"],
        "routes_py_under_300_lines": inventory["routes_py_under_300_lines"],
        "total_mobile_route_decorator_count": inventory["total_mobile_route_decorator_count"],
        "expected_contract_route_count": EXPECTED_ROUTE_COUNT,
        "direct_contract_ok": inventory["route_contract_count_expected"],
        "compile_ok": compile_ok,
        "app_factory_ok": bool(app_factory_result.get("ok")),
        "secret_gate_ok": bool(secret_result.get("ok")),
        "secret_gate_finding_count": secret_finding_count,
        "pytest_ok": bool(pytest_result.get("ok")),
        "pytest_mode": pytest_result.get("mode", "pytest_targeted_android_responsive_visual_regression_evidence_suite_p6b"),
        "active_scope": {},
        "inventory": inventory,
        "visual_regression_evidence_suite": {
            "ok": visual_regression_evidence_suite_ok,
            "source_p6a_report": str(root / P6A_REPORT_REL),
            "source_p5f_report": str(root / P5F_REPORT_REL),
            "guide": str(root / P6A_GUIDE_REL),
            "findings_template": str(root / P6A_FINDINGS_TEMPLATE_REL),
            "evidence_doc": docs["evidence_doc"],
            "findings_index": docs["findings_index"],
            "visual_dirs": visual_dirs["dirs"],
            "screenshot_count": visual_dirs["screenshot_count"],
            "screenshots": visual_dirs["screenshots"],
            "finding_count": visual_dirs["finding_count"],
            "finding_files": visual_dirs["finding_files"],
            "device_count": int(p6a.get("android_device_matrix_count") or p5f.get("android_device_matrix_count") or 0),
            "target_surface_count": int(p6a.get("target_surface_count") or p5f.get("target_surface_count") or 0),
            "expected_surface_flags": p6a.get("visual_regression_evidence", {}).get("expected_surface_flags", []),
        },
        "compile_results": compile_results,
        "app_factory_smoke": app_factory_result,
        "secret_gate": secret_result,
        "pytest": pytest_result,
        "ci_commands": [
            "python -m pip install -r requirements-dev.txt",
            "python -m pytest tests/architecture -q",
            "python scripts/quality/bys360_android_responsive_visual_regression_evidence_suite_gate_p6b.py --root . --compile-all --app-factory --secret-gate --pytest-gate",
        ],
        "report": str(root / REPORT_REL),
        "next_actions": [
            "P6B temizse Android responsive gorsel regresyon kanit suite'i hazir kabul edilebilir.",
            "Gercek screenshot/bulgu dosyalari eklenirse ayni gate bunlari sayip rapora dahil eder.",
        ],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=PACKAGE)
    parser.add_argument("--root", default=".")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--app-factory", action="store_true")
    parser.add_argument("--secret-gate", action="store_true")
    parser.add_argument("--pytest-gate", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = build_report(root, args.compile_all, args.app_factory, args.secret_gate, args.pytest_gate)
    report_path = root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_keys = [
        "ok",
        "package",
        "android_responsive_visual_regression_evidence_suite_gate_ok",
        "visual_regression_evidence_suite_ok",
        "p6a_visual_regression_report_ok",
        "p5f_final_evidence_report_ok",
        "visual_regression_guide_ok",
        "visual_regression_findings_template_ok",
        "visual_regression_evidence_doc_ok",
        "findings_index_ok",
        "screenshot_evidence_optional_ok",
        "screenshot_count",
        "finding_count",
        "direct_contract_ok",
        "compile_ok",
        "app_factory_ok",
        "secret_gate_ok",
        "secret_gate_finding_count",
        "pytest_ok",
        "pytest_mode",
        "report",
    ]
    print(json.dumps({key: report.get(key) for key in summary_keys}, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
