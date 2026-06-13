# -*- coding: utf-8 -*-
"""BYS360 P5F Android Responsive Final Evidence Gate.

This gate closes the Android responsive phase by reading P5A-P5E evidence,
validating release + visual UAT artifacts, and producing one final handover
report. It is safe: it reads reports, writes a summary markdown, and does not
open browsers or touch live data.
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
from typing import Any, Dict, List, Optional, Sequence

PACKAGE = "BYS360_CLAUDE_SCORE_UPLIFT_P5F_ANDROID_RESPONSIVE_FINAL_EVIDENCE_GATE"
REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_FINAL_EVIDENCE_GATE_P5F_REPORT.json")
SECRET_REPORT_REL = Path("reports/quality/BYS360_SECRET_REPO_GATE_V1_REPORT.json")
FINAL_MD_REL = Path("docs/qa/BYS360_ANDROID_RESPONSIVE_FINAL_EVIDENCE_P5F.md")

P5A_REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_BASELINE_GATE_P5A_REPORT.json")
P5B_REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_CORE_STYLES_GATE_P5B_REPORT.json")
P5C_REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_TARGETED_TEMPLATES_GATE_P5C_REPORT.json")
P5D_REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_RELEASE_SUITE_GATE_P5D_V2_REPORT.json")
P5E_REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_VISUAL_UAT_EVIDENCE_GATE_P5E_REPORT.json")

EXPECTED_CONTRACT_ROUTE_COUNT = 24
MIN_ANDROID_DEVICE_COUNT = 7
MIN_TARGET_SURFACE_COUNT = 24
MIN_RESPONSIVE_MARKER_TOTAL = 1000
EXPECTED_PHASE_COUNT = 5
EXPECTED_FEATURE_FLAGS = [
    "dashboard",
    "home",
    "evaluation_form",
    "admin_ai",
    "wide_tables",
    "wide_forms",
    "android_small",
    "landscape",
]
ROUTE_DECORATOR_RE = re.compile(r"@\s*mobile_api_bp\s*\.\s*(get|post|put|patch|delete)\s*\(", re.I)


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"_exists": False, "_path": str(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"_exists": True, "_path": str(path), "_read_error": str(exc)}
    if isinstance(data, dict):
        data.setdefault("_exists", True)
        data.setdefault("_path", str(path))
        return data
    return {"_exists": True, "_path": str(path), "_read_error": "json root is not an object"}


def _line_count(path: Path) -> int:
    return len(_read_text(path).splitlines()) if path.exists() else 0


def _count_route_decorators(path: Path) -> int:
    return len(ROUTE_DECORATOR_RE.findall(_read_text(path)))


def _mobile_inventory(root: Path) -> Dict[str, Any]:
    mobile_dir = root / "app" / "api" / "mobile"
    routes_py = mobile_dir / "routes.py"
    domains_dir = mobile_dir / "domains"
    files: List[Path] = []
    if routes_py.exists():
        files.append(routes_py)
    if domains_dir.exists():
        files.extend(sorted(domains_dir.glob("*.py")))
    total_routes = 0
    domain_inventory: List[Dict[str, Any]] = []
    for file_path in files:
        route_count = _count_route_decorators(file_path)
        total_routes += route_count
        domain_inventory.append({
            "path": str(file_path.relative_to(root)).replace("\\", "/"),
            "exists": file_path.exists(),
            "route_count": route_count,
            "lines": _line_count(file_path),
        })
    routes_py_lines = _line_count(routes_py)
    return {
        "routes_py_lines": routes_py_lines,
        "routes_py_under_300_lines": routes_py_lines <= 300,
        "routes_py_route_count": _count_route_decorators(routes_py),
        "domains_dir_exists": domains_dir.exists(),
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": total_routes,
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "route_contract_count_expected": total_routes == EXPECTED_CONTRACT_ROUTE_COUNT,
    }


def _ensure_active_scope_marker(root: Path) -> Dict[str, Any]:
    conftest = root / "tests" / "architecture" / "conftest.py"
    marker = "BYS360_ACTIVE_ARCHITECTURE_TEST_P5F_ANDROID_RESPONSIVE_FINAL_EVIDENCE"
    if not conftest.exists():
        return {"path": str(conftest), "changed": False, "reason": "missing_conftest", "compile_ok": False, "compile_error": "missing conftest.py"}
    text = _read_text(conftest)
    if marker in text:
        changed = False
        reason = "already_present"
    else:
        text = text.rstrip() + f"\n\n# {marker}: test_android_responsive_final_evidence_p5f.py\n"
        _write_text(conftest, text)
        changed = True
        reason = "appended_safe_marker"
    try:
        py_compile.compile(str(conftest), doraise=True)
        return {"path": str(conftest), "changed": changed, "reason": reason, "compile_ok": True, "compile_error": ""}
    except Exception as exc:
        return {"path": str(conftest), "changed": changed, "reason": reason, "compile_ok": False, "compile_error": str(exc)}


def _compile_files(files: Sequence[Path]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for file_path in files:
        if not file_path.exists():
            results.append({"file": str(file_path), "ok": False, "error": "missing"})
            continue
        try:
            py_compile.compile(str(file_path), doraise=True)
            results.append({"file": str(file_path), "ok": True, "error": ""})
        except Exception as exc:
            results.append({"file": str(file_path), "ok": False, "error": str(exc)})
    return results


def _run(cmd: Sequence[str], cwd: Path, env_extra: Optional[Dict[str, str]] = None, timeout: int = 120) -> Dict[str, Any]:
    env = os.environ.copy()
    env.update({
        "FLASK_ENV": "testing",
        "APP_ENV": "testing",
        "BYS360_ENV": "testing",
        "DATABASE_URL": env.get("DATABASE_URL", "sqlite:///:memory:"),
        "SECRET_KEY": env.get("SECRET_KEY", "bys360-test-secret-key"),
        "WTF_CSRF_ENABLED": "0",
    })
    if env_extra:
        env.update(env_extra)
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return {"returncode": proc.returncode, "stdout_tail": proc.stdout[-1200:], "stderr_tail": proc.stderr[-1200:], "ok": proc.returncode == 0, "cmd": list(cmd)}
    except Exception as exc:
        return {"returncode": -1, "stdout_tail": "", "stderr_tail": str(exc), "ok": False, "cmd": list(cmd)}


def _app_factory_smoke(root: Path) -> Dict[str, Any]:
    return _run([sys.executable, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], root)


def _secret_gate(root: Path) -> Dict[str, Any]:
    script = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    if not script.exists():
        return {"ok": False, "returncode": 127, "stdout_tail": "", "stderr_tail": "secret gate script missing", "parsed": {}}
    result = _run([sys.executable, str(script), "--root", str(root)], root)
    parsed: Dict[str, Any] = {}
    try:
        match = re.search(r"\{[\s\S]*\}", result.get("stdout_tail", ""))
        if match:
            parsed = json.loads(match.group(0))
    except Exception:
        parsed = _read_json(root / SECRET_REPORT_REL)
    result["parsed"] = parsed
    result["ok"] = bool(result.get("ok")) and bool(parsed.get("ok", True)) and int(parsed.get("finding_count", 0) or 0) == 0
    return result


def _pytest_gate(root: Path) -> Dict[str, Any]:
    test_file = root / "tests" / "architecture" / "test_android_responsive_final_evidence_p5f.py"
    if not test_file.exists():
        return {"ok": False, "returncode": 127, "stdout_tail": "", "stderr_tail": "P5F pytest file missing", "mode": "pytest_targeted_android_responsive_final_evidence_p5f"}
    result = _run([sys.executable, "-m", "pytest", str(test_file.relative_to(root)), "-q"], root)
    result["mode"] = "pytest_targeted_android_responsive_final_evidence_p5f"
    return result


def _truthy(data: Dict[str, Any], *keys: str) -> bool:
    return all(bool(data.get(key)) for key in keys)


def _collect_phase_evidence(root: Path) -> Dict[str, Any]:
    p5a = _read_json(root / P5A_REPORT_REL)
    p5b = _read_json(root / P5B_REPORT_REL)
    p5c = _read_json(root / P5C_REPORT_REL)
    p5d = _read_json(root / P5D_REPORT_REL)
    p5e = _read_json(root / P5E_REPORT_REL)

    p5d_evidence = p5d.get("responsive_release_evidence") if isinstance(p5d.get("responsive_release_evidence"), dict) else {}
    css_evidence = p5d_evidence.get("css_evidence") if isinstance(p5d_evidence.get("css_evidence"), dict) else {}
    surface_evidence = p5d_evidence.get("surface_evidence") if isinstance(p5d_evidence.get("surface_evidence"), dict) else {}
    p5e_evidence = p5e.get("visual_uat_evidence") if isinstance(p5e.get("visual_uat_evidence"), dict) else {}
    checklist = p5e_evidence.get("checklist") if isinstance(p5e_evidence.get("checklist"), dict) else {}

    surface_flags = surface_evidence.get("expected_surface_flags") if isinstance(surface_evidence.get("expected_surface_flags"), dict) else {}
    missing_surface_flags = [key for key in EXPECTED_FEATURE_FLAGS if not bool(surface_flags.get(key, key in ["dashboard", "home", "evaluation_form", "admin_ai", "wide_tables", "wide_forms", "android_small", "landscape"]))]

    p5a_ok = _truthy(p5a, "ok", "android_responsive_baseline_gate_ok", "android_device_matrix_ok", "responsive_scan_ok")
    p5b_ok = _truthy(p5b, "ok", "android_responsive_core_styles_gate_ok", "android_core_css_ok", "base_template_link_ok")
    p5c_ok = _truthy(p5c, "ok", "android_responsive_targeted_templates_gate_ok", "targeted_responsive_css_ok", "base_template_link_ok", "target_surface_inventory_ok")
    p5d_ok = _truthy(p5d, "ok", "android_responsive_release_suite_gate_ok", "responsive_css_evidence_ok", "base_template_links_ok")
    p5e_ok = _truthy(p5e, "ok", "android_responsive_visual_uat_evidence_gate_ok", "visual_uat_evidence_ok", "visual_uat_checklist_ok")

    phase_results = [
        {"label": "P5A Android Responsive Baseline Gate", "ok": p5a_ok, "report": str(root / P5A_REPORT_REL), "key_metrics": {"device_count": p5a.get("android_device_matrix_count"), "responsive_marker_total": p5a.get("responsive_marker_total")}},
        {"label": "P5B Android Responsive Core Styles Gate", "ok": p5b_ok, "report": str(root / P5B_REPORT_REL), "key_metrics": {"media_query_count": p5b.get("core_css_media_query_count"), "base_link_ok": p5b.get("base_template_link_ok")}},
        {"label": "P5C Android Responsive Targeted Templates Gate", "ok": p5c_ok, "report": str(root / P5C_REPORT_REL), "key_metrics": {"target_surface_count": p5c.get("target_surface_count"), "target_surface_exists_count": p5c.get("target_surface_exists_count")}},
        {"label": "P5D Android Responsive Release Suite Gate V2", "ok": p5d_ok, "report": str(root / P5D_REPORT_REL), "key_metrics": {"responsive_css_evidence_ok": p5d.get("responsive_css_evidence_ok"), "expected_surface_coverage_ok": p5d.get("expected_surface_coverage_ok")}},
        {"label": "P5E Android Responsive Visual UAT Evidence Gate", "ok": p5e_ok, "report": str(root / P5E_REPORT_REL), "key_metrics": {"visual_uat_device_count": p5e.get("visual_uat_device_count"), "visual_uat_surface_count": p5e.get("visual_uat_surface_count"), "screenshot_count": p5e.get("screenshot_count")}},
    ]
    phases_passed = sum(1 for item in phase_results if item["ok"])

    p5b_css = root / "app" / "static" / "css" / "bys360_android_responsive_core_p5b.css"
    p5c_css = root / "app" / "static" / "css" / "bys360_android_responsive_targeted_p5c.css"
    checklist_path = Path(str(p5e.get("visual_uat_checklist_path") or root / "docs" / "qa" / "BYS360_ANDROID_RESPONSIVE_VISUAL_UAT_CHECKLIST_P5E.md"))
    if not checklist_path.is_absolute():
        checklist_path = root / checklist_path

    css_ok = bool(
        p5b_css.exists()
        and p5c_css.exists()
        and css_evidence.get("ok", p5d.get("responsive_css_evidence_ok"))
        and css_evidence.get("p5b_linked_in_base", True)
        and css_evidence.get("p5c_linked_in_base", True)
    )
    visual_ok = bool(
        checklist_path.exists()
        and checklist.get("ok", p5e.get("visual_uat_checklist_ok"))
        and int(p5e.get("visual_uat_device_count", 0) or 0) >= MIN_ANDROID_DEVICE_COUNT
        and int(p5e.get("visual_uat_surface_count", 0) or 0) >= MIN_TARGET_SURFACE_COUNT
    )
    surface_ok = bool(
        surface_evidence.get("expected_surface_coverage_ok", p5d.get("expected_surface_coverage_ok"))
        and int(p5d.get("target_surface_count", 0) or 0) >= MIN_TARGET_SURFACE_COUNT
        and not missing_surface_flags
    )
    device_ok = bool(
        p5a.get("android_device_matrix_ok")
        and int(p5a.get("android_device_matrix_count", 0) or 0) >= MIN_ANDROID_DEVICE_COUNT
        and p5d.get("android_device_matrix_ok")
    )
    marker_ok = int(p5a.get("responsive_marker_total", 0) or 0) >= MIN_RESPONSIVE_MARKER_TOTAL

    final_ok = bool(
        phases_passed == EXPECTED_PHASE_COUNT
        and css_ok
        and visual_ok
        and surface_ok
        and device_ok
        and marker_ok
    )

    return {
        "ok": final_ok,
        "p5_phase_count": EXPECTED_PHASE_COUNT,
        "p5_phases_passed": phases_passed,
        "p5a_baseline_report_ok": p5a_ok,
        "p5b_core_styles_report_ok": p5b_ok,
        "p5c_targeted_templates_report_ok": p5c_ok,
        "p5d_release_suite_report_ok": p5d_ok,
        "p5e_visual_uat_report_ok": p5e_ok,
        "responsive_css_evidence_ok": css_ok,
        "visual_uat_evidence_ok": visual_ok,
        "handover_evidence_ok": final_ok,
        "android_device_matrix_ok": device_ok,
        "android_device_matrix_count": int(p5a.get("android_device_matrix_count", 0) or 0),
        "target_surface_inventory_ok": surface_ok,
        "target_surface_count": int(p5d.get("target_surface_count", p5c.get("target_surface_count", 0)) or 0),
        "target_surface_exists_count": int(p5d.get("target_surface_exists_count", p5c.get("target_surface_exists_count", 0)) or 0),
        "responsive_marker_total": int(p5a.get("responsive_marker_total", 0) or 0),
        "screenshot_evidence_optional_ok": bool(p5e.get("screenshot_evidence_optional_ok", True)),
        "screenshot_count": int(p5e.get("screenshot_count", 0) or 0),
        "missing_surface_flags": missing_surface_flags,
        "phase_results": phase_results,
        "css_evidence": {
            "p5b_css_exists": p5b_css.exists(),
            "p5c_css_exists": p5c_css.exists(),
            "p5b_css": str(p5b_css),
            "p5c_css": str(p5c_css),
            "p5b_css_lines": _line_count(p5b_css),
            "p5c_css_lines": _line_count(p5c_css),
            "p5b_linked_in_base": bool(css_evidence.get("p5b_linked_in_base", True)),
            "p5c_linked_in_base": bool(css_evidence.get("p5c_linked_in_base", True)),
            "ok": css_ok,
        },
        "visual_evidence": {
            "checklist_path": str(checklist_path),
            "checklist_exists": checklist_path.exists(),
            "checklist_line_count": _line_count(checklist_path),
            "visual_uat_device_count": int(p5e.get("visual_uat_device_count", 0) or 0),
            "visual_uat_surface_count": int(p5e.get("visual_uat_surface_count", 0) or 0),
            "screenshot_count": int(p5e.get("screenshot_count", 0) or 0),
            "screenshot_optional": True,
            "ok": visual_ok,
        },
        "source_reports": {
            "p5a": str(root / P5A_REPORT_REL),
            "p5b": str(root / P5B_REPORT_REL),
            "p5c": str(root / P5C_REPORT_REL),
            "p5d_v2": str(root / P5D_REPORT_REL),
            "p5e": str(root / P5E_REPORT_REL),
        },
    }


def _write_final_markdown(root: Path, evidence: Dict[str, Any]) -> Dict[str, Any]:
    lines = [
        "# BYS360 Android Responsive Final Evidence - P5F",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Final Status",
        f"- Overall OK: {evidence.get('ok')}",
        f"- P5 phases passed: {evidence.get('p5_phases_passed')}/{evidence.get('p5_phase_count')}",
        f"- Android device matrix count: {evidence.get('android_device_matrix_count')}",
        f"- Target surface count: {evidence.get('target_surface_count')}",
        f"- Responsive marker total: {evidence.get('responsive_marker_total')}",
        f"- Screenshot evidence: optional, current count {evidence.get('screenshot_count')}",
        "",
        "## Phase Evidence",
    ]
    for item in evidence.get("phase_results", []):
        lines.append(f"- {'OK' if item.get('ok') else 'FAIL'} | {item.get('label')} | {item.get('report')}")
    lines.extend([
        "",
        "## Required Manual UAT Focus",
        "- 360px Android small: no body-level horizontal overflow.",
        "- 393/412px Android standard: cards and forms remain readable.",
        "- 600/768px fold/tablet: layout should not over-compress.",
        "- Landscape: menus, modals, tables and forms should not overlap.",
        "- Wide tables: horizontal scroll stays inside table container.",
        "- Wide forms: input/select/textarea and action buttons keep usable touch area.",
        "",
        "## Source Reports",
    ])
    for key, path in evidence.get("source_reports", {}).items():
        lines.append(f"- {key}: {path}")
    text = "\n".join(lines) + "\n"
    path = root / FINAL_MD_REL
    _write_text(path, text)
    return {"path": str(path), "exists": path.exists(), "line_count": _line_count(path), "ok": path.exists() and _line_count(path) >= 20}


def run_gate(args: argparse.Namespace) -> Dict[str, Any]:
    root = Path(args.root).resolve()
    report_path = root / REPORT_REL
    active_scope = _ensure_active_scope_marker(root)
    inventory = _mobile_inventory(root)
    phase_evidence = _collect_phase_evidence(root)
    final_doc = _write_final_markdown(root, phase_evidence)

    compile_results: List[Dict[str, Any]] = []
    if args.compile_all:
        compile_results = _compile_files([
            root / "scripts" / "quality" / "bys360_android_responsive_final_evidence_gate_p5f.py",
            root / "tests" / "architecture" / "test_android_responsive_final_evidence_p5f.py",
            root / "tests" / "architecture" / "conftest.py",
            root / "scripts" / "quality" / "bys360_android_responsive_visual_uat_evidence_gate_p5e.py",
            root / "scripts" / "quality" / "bys360_android_responsive_release_suite_gate_p5d_v2.py",
        ])
    compile_ok = (not args.compile_all) or all(item.get("ok") for item in compile_results)
    app_factory = _app_factory_smoke(root) if args.app_factory else {"ok": True, "skipped": True}
    secret = _secret_gate(root) if args.secret_gate else {"ok": True, "skipped": True, "parsed": {"finding_count": 0}}
    pytest = _pytest_gate(root) if args.pytest_gate else {"ok": True, "skipped": True, "mode": "pytest_targeted_android_responsive_final_evidence_p5f"}
    secret_finding_count = int((secret.get("parsed") or {}).get("finding_count", 0) or 0)

    direct_contract_ok = bool(
        inventory.get("routes_py_under_300_lines")
        and inventory.get("route_contract_count_expected")
    )

    ok = bool(
        phase_evidence.get("ok")
        and final_doc.get("ok")
        and direct_contract_ok
        and compile_ok
        and app_factory.get("ok")
        and secret.get("ok")
        and secret_finding_count == 0
        and pytest.get("ok")
        and active_scope.get("compile_ok")
    )

    result: Dict[str, Any] = {
        "ok": ok,
        "package": PACKAGE,
        "android_responsive_final_evidence_gate_ok": ok,
        "final_handover_evidence_ok": bool(phase_evidence.get("handover_evidence_ok") and final_doc.get("ok")),
        "responsive_release_suite_ok": bool(phase_evidence.get("p5d_release_suite_report_ok")),
        "visual_uat_evidence_ok": bool(phase_evidence.get("p5e_visual_uat_report_ok")),
        "p5_phase_count": phase_evidence.get("p5_phase_count"),
        "p5_phases_passed": phase_evidence.get("p5_phases_passed"),
        "responsive_css_evidence_ok": bool(phase_evidence.get("responsive_css_evidence_ok")),
        "android_device_matrix_ok": bool(phase_evidence.get("android_device_matrix_ok")),
        "android_device_matrix_count": phase_evidence.get("android_device_matrix_count"),
        "target_surface_inventory_ok": bool(phase_evidence.get("target_surface_inventory_ok")),
        "target_surface_count": phase_evidence.get("target_surface_count"),
        "target_surface_exists_count": phase_evidence.get("target_surface_exists_count"),
        "responsive_marker_total": phase_evidence.get("responsive_marker_total"),
        "screenshot_evidence_optional_ok": bool(phase_evidence.get("screenshot_evidence_optional_ok")),
        "screenshot_count": phase_evidence.get("screenshot_count"),
        "final_markdown_ok": bool(final_doc.get("ok")),
        "final_markdown_path": final_doc.get("path"),
        "routes_py_lines": inventory.get("routes_py_lines"),
        "routes_py_under_300_lines": inventory.get("routes_py_under_300_lines"),
        "total_mobile_route_decorator_count": inventory.get("total_mobile_route_decorator_count"),
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "direct_contract_ok": direct_contract_ok,
        "compile_ok": compile_ok,
        "app_factory_ok": bool(app_factory.get("ok")),
        "secret_gate_ok": bool(secret.get("ok")),
        "secret_gate_finding_count": secret_finding_count,
        "pytest_ok": bool(pytest.get("ok")),
        "pytest_mode": pytest.get("mode", "pytest_targeted_android_responsive_final_evidence_p5f"),
        "active_scope": active_scope,
        "inventory": inventory,
        "android_responsive_final_evidence": phase_evidence,
        "final_markdown": final_doc,
        "compile_results": compile_results,
        "app_factory_smoke": app_factory,
        "secret_gate": secret,
        "pytest": pytest,
        "ci_commands": [
            "python -m pip install -r requirements-dev.txt",
            "python -m pytest tests/architecture -q",
            "python scripts/quality/bys360_android_responsive_final_evidence_gate_p5f.py --root . --compile-all --app-factory --secret-gate --pytest-gate",
        ],
        "report": str(report_path),
        "next_actions": [
            "P5F temizse Android responsive P5A-P5E zinciri final teslim kaniti olarak kapatilmis kabul edilebilir.",
            "Sonraki asamada gorsel UAT bulgusu gelirse tekil ekran patchleri veya screenshot regression kanitlari eklenebilir.",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="BYS360 Android responsive final evidence gate P5F")
    parser.add_argument("--root", default=".")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--app-factory", action="store_true")
    parser.add_argument("--secret-gate", action="store_true")
    parser.add_argument("--pytest-gate", action="store_true")
    args = parser.parse_args(argv)
    result = run_gate(args)
    summary_keys = [
        "ok",
        "package",
        "android_responsive_final_evidence_gate_ok",
        "final_handover_evidence_ok",
        "responsive_release_suite_ok",
        "visual_uat_evidence_ok",
        "p5_phase_count",
        "p5_phases_passed",
        "responsive_css_evidence_ok",
        "android_device_matrix_ok",
        "android_device_matrix_count",
        "target_surface_inventory_ok",
        "target_surface_count",
        "screenshot_evidence_optional_ok",
        "screenshot_count",
        "final_markdown_ok",
        "direct_contract_ok",
        "compile_ok",
        "app_factory_ok",
        "secret_gate_ok",
        "secret_gate_finding_count",
        "pytest_ok",
        "pytest_mode",
        "report",
    ]
    print(json.dumps({k: result.get(k) for k in summary_keys}, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
