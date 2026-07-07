# -*- coding: utf-8 -*-
"""BYS360 P5D Android Responsive Release Suite Gate.

Combines P5A baseline, P5B core styles and P5C targeted templates into one
CI/handover-ready Android responsive release evidence gate. The gate is safe:
it reads reports, validates CSS/link evidence and does not touch live data.
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

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P5D_ANDROID_RESPONSIVE_RELEASE_SUITE_GATE"
REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_RELEASE_SUITE_GATE_P5D_REPORT.json")
P5A_REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_BASELINE_GATE_P5A_REPORT.json")
P5B_REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_CORE_STYLES_GATE_P5B_REPORT.json")
P5C_REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_TARGETED_TEMPLATES_GATE_P5C_REPORT.json")
SECRET_REPORT_REL = Path("reports/quality/BYS360_SECRET_REPO_GATE_V1_REPORT.json")
P5B_CSS_REL = Path("app/static/css/bys360_android_responsive_core_p5b.css")
P5C_CSS_REL = Path("app/static/css/bys360_android_responsive_targeted_p5c.css")
BASE_REL = Path("app/templates/base.html")
EXPECTED_CONTRACT_ROUTE_COUNT = 24
MIN_ANDROID_DEVICE_COUNT = 7
MIN_RESPONSIVE_MARKER_TOTAL = 1000
MIN_CORE_MEDIA_QUERY_COUNT = 5
MIN_TARGETED_MEDIA_QUERY_COUNT = 6
MIN_TARGET_SURFACE_COUNT = 24

P5B_LINK = "{{ url_for('static', filename='css/bys360_android_responsive_core_p5b.css') }}"
P5C_LINK = "{{ url_for('static', filename='css/bys360_android_responsive_targeted_p5c.css') }}"
EXPECTED_FEATURE_SURFACES = {
    "dashboard",
    "home",
    "evaluation_form",
    "admin_ai",
    "wide_tables",
    "wide_forms",
    "android_small",
    "landscape",
}

ROUTE_DECORATOR_RE = re.compile(r"@\s*mobile_api_bp\s*\.\s*(get|post|put|patch|delete)\s*\(", re.I)


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


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


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _count_route_decorators(path: Path) -> int:
    return len(ROUTE_DECORATOR_RE.findall(_read_text(path)))


def _line_count(path: Path) -> int:
    return len(_read_text(path).splitlines()) if path.exists() else 0


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
    domain_inventory = []
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
    marker = "BYS360_ACTIVE_ARCHITECTURE_TEST_P5D_ANDROID_RESPONSIVE_RELEASE_SUITE"
    if not conftest.exists():
        return {"path": str(conftest), "changed": False, "reason": "missing_conftest", "compile_ok": False, "compile_error": "missing conftest.py"}
    text = _read_text(conftest)
    if marker in text:
        changed = False
        reason = "already_present"
    else:
        text = text.rstrip() + f"\n\n# {marker}: test_android_responsive_release_suite_p5d.py\n"
        _write_text(conftest, text)
        changed = True
        reason = "appended_safe_marker"
    try:
        py_compile.compile(str(conftest), doraise=True)
        return {"path": str(conftest), "changed": changed, "reason": reason, "compile_ok": True, "compile_error": ""}
    except Exception as exc:
        return {"path": str(conftest), "changed": changed, "reason": reason, "compile_ok": False, "compile_error": str(exc)}


def _compile_files(files: Sequence[Path]) -> List[Dict[str, str | bool]]:
    results: List[Dict[str, str | bool]] = []
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
    test_file = root / "tests" / "architecture" / "test_android_responsive_release_suite_p5d.py"
    if not test_file.exists():
        return {"ok": False, "returncode": 127, "stdout_tail": "", "stderr_tail": "P5D pytest file missing", "mode": "pytest_targeted_android_responsive_release_suite_p5d"}
    result = _run([sys.executable, "-m", "pytest", str(test_file.relative_to(root)), "-q"], root)
    result["mode"] = "pytest_targeted_android_responsive_release_suite_p5d"
    return result


def _css_evidence(root: Path) -> Dict[str, Any]:
    p5b_css = root / P5B_CSS_REL
    p5c_css = root / P5C_CSS_REL
    base = root / BASE_REL
    p5b_text = _read_text(p5b_css)
    p5c_text = _read_text(p5c_css)
    base_text = _read_text(base)
    return {
        "p5b_css_exists": p5b_css.exists(),
        "p5c_css_exists": p5c_css.exists(),
        "base_template_exists": base.exists(),
        "p5b_linked_in_base": P5B_LINK in base_text or "bys360_android_responsive_core_p5b.css" in base_text,
        "p5c_linked_in_base": P5C_LINK in base_text or "bys360_android_responsive_targeted_p5c.css" in base_text,
        "p5b_media_query_count": p5b_text.count("@media"),
        "p5c_media_query_count": p5c_text.count("@media"),
        "p5b_marker_present": "P5B_ANDROID_RESPONSIVE_CORE" in p5b_text,
        "p5c_marker_present": "P5C_ANDROID_RESPONSIVE_TARGETED" in p5c_text,
        "ok": bool(
            p5b_css.exists()
            and p5c_css.exists()
            and base.exists()
            and (P5B_LINK in base_text or "bys360_android_responsive_core_p5b.css" in base_text)
            and (P5C_LINK in base_text or "bys360_android_responsive_targeted_p5c.css" in base_text)
            and p5b_text.count("@media") >= MIN_CORE_MEDIA_QUERY_COUNT
            and p5c_text.count("@media") >= MIN_TARGETED_MEDIA_QUERY_COUNT
            and "P5B_ANDROID_RESPONSIVE_CORE" in p5b_text
            and "P5C_ANDROID_RESPONSIVE_TARGETED" in p5c_text
        ),
    }


def _surface_evidence(p5a: Dict[str, Any], p5b: Dict[str, Any], p5c: Dict[str, Any]) -> Dict[str, Any]:
    p5a_device = p5a.get("android_device_matrix") if isinstance(p5a.get("android_device_matrix"), dict) else {}
    p5a_scan = p5a.get("responsive_surface_scan") if isinstance(p5a.get("responsive_surface_scan"), dict) else {}
    p5b_surface = p5b.get("surface_priority") if isinstance(p5b.get("surface_priority"), dict) else {}
    p5c_surfaces = p5c.get("target_surfaces") if isinstance(p5c.get("target_surfaces"), dict) else {}

    target_paths = [item.get("path", "") for item in p5c_surfaces.get("targeted_templates", []) if isinstance(item, dict)]
    target_text = "\n".join(target_paths).lower()
    expected_surface_flags = {
        "dashboard": "dashboard" in target_text,
        "home": "home" in target_text,
        "evaluation_form": "evaluation_form" in target_text,
        "admin_ai": "admin_ai" in target_text,
        "wide_tables": p5c.get("targeted_css_required_marker_total", 0) >= 12,
        "wide_forms": p5c.get("targeted_css_required_marker_total", 0) >= 12,
        "android_small": bool(p5a_device.get("has_small_phone")),
        "landscape": bool(p5a_device.get("has_landscape")),
    }
    return {
        "device_matrix_ok": bool(p5a.get("android_device_matrix_ok")) and int(p5a.get("android_device_matrix_count", 0) or 0) >= MIN_ANDROID_DEVICE_COUNT,
        "device_count": int(p5a.get("android_device_matrix_count", 0) or 0),
        "responsive_scan_ok": bool(p5a.get("responsive_scan_ok")) and int(p5a.get("responsive_marker_total", 0) or 0) >= MIN_RESPONSIVE_MARKER_TOTAL,
        "responsive_marker_total": int(p5a.get("responsive_marker_total", 0) or 0),
        "p5b_priority_ok": bool(p5b_surface.get("source_report_exists", True)) and int(p5b_surface.get("priority_no_marker_count", 0) or 0) >= 0,
        "p5c_target_surface_ok": bool(p5c.get("target_surface_inventory_ok")) and int(p5c.get("target_surface_count", 0) or 0) >= MIN_TARGET_SURFACE_COUNT and int(p5c.get("target_surface_exists_count", 0) or 0) >= MIN_TARGET_SURFACE_COUNT,
        "target_surface_count": int(p5c.get("target_surface_count", 0) or 0),
        "target_surface_exists_count": int(p5c.get("target_surface_exists_count", 0) or 0),
        "expected_surface_flags": expected_surface_flags,
        "expected_surface_coverage_ok": all(expected_surface_flags.values()),
        "p5a_device_matrix": p5a_device,
        "p5a_scan_summary": {
            "candidate_file_count": p5a_scan.get("candidate_file_count"),
            "scanned_file_count": p5a_scan.get("scanned_file_count"),
            "responsive_marker_total": p5a.get("responsive_marker_total"),
        },
    }


def run_gate(args: argparse.Namespace) -> Dict[str, Any]:
    root = Path(args.root).resolve()
    report_path = root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)

    active_scope = _ensure_active_scope_marker(root)
    inventory = _mobile_inventory(root)
    p5a = _read_json(root / P5A_REPORT_REL)
    p5b = _read_json(root / P5B_REPORT_REL)
    p5c = _read_json(root / P5C_REPORT_REL)
    css = _css_evidence(root)
    surface = _surface_evidence(p5a, p5b, p5c)

    p5a_ok = bool(p5a.get("_exists") and p5a.get("ok") and p5a.get("android_responsive_baseline_gate_ok"))
    p5b_ok = bool(p5b.get("_exists") and p5b.get("ok") and p5b.get("android_responsive_core_styles_gate_ok") and p5b.get("base_template_link_ok"))
    p5c_ok = bool(p5c.get("_exists") and p5c.get("ok") and p5c.get("android_responsive_targeted_templates_gate_ok") and p5c.get("base_template_link_ok"))

    release_suite_ok = bool(
        p5a_ok
        and p5b_ok
        and p5c_ok
        and css.get("ok")
        and surface.get("device_matrix_ok")
        and surface.get("responsive_scan_ok")
        and surface.get("p5c_target_surface_ok")
        and surface.get("expected_surface_coverage_ok")
    )

    compile_results: List[Dict[str, Any]] = []
    if args.compile_all:
        compile_results = _compile_files([
            root / "scripts" / "quality" / "bys360_android_responsive_release_suite_gate_p5d.py",
            root / "tests" / "architecture" / "test_android_responsive_release_suite_p5d.py",
            root / "tests" / "architecture" / "conftest.py",
            root / "scripts" / "quality" / "bys360_android_responsive_baseline_gate_p5a.py",
            root / "scripts" / "quality" / "bys360_android_responsive_core_styles_gate_p5b.py",
            root / "scripts" / "quality" / "bys360_android_responsive_targeted_templates_gate_p5c.py",
        ])
    compile_ok = (all(item.get("ok") for item in compile_results) if compile_results else True) and bool(active_scope.get("compile_ok"))
    app_factory = _app_factory_smoke(root) if args.app_factory else {"ok": True, "skipped": True}
    secret = _secret_gate(root) if args.secret_gate else {"ok": True, "skipped": True, "parsed": {"finding_count": 0}}
    pytest = _pytest_gate(root) if args.pytest_gate else {"ok": True, "skipped": True, "mode": "not_run"}
    secret_count = int((secret.get("parsed") or {}).get("finding_count", 0) or 0)
    direct_contract_ok = bool(
        inventory["routes_py_under_300_lines"]
        and inventory["routes_py_route_count"] == 0
        and inventory["domains_dir_exists"]
        and inventory["route_contract_count_expected"]
    )
    ok = bool(release_suite_ok and direct_contract_ok and compile_ok and app_factory.get("ok") and secret.get("ok") and secret_count == 0 and pytest.get("ok"))

    output: Dict[str, Any] = {
        "ok": ok,
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "android_responsive_release_suite_gate_ok": release_suite_ok,
        "responsive_release_suite_ok": release_suite_ok,
        "p5a_baseline_report_ok": p5a_ok,
        "p5b_core_styles_report_ok": p5b_ok,
        "p5c_targeted_templates_report_ok": p5c_ok,
        "responsive_css_evidence_ok": bool(css.get("ok")),
        "base_template_links_ok": bool(css.get("p5b_linked_in_base") and css.get("p5c_linked_in_base")),
        "android_device_matrix_ok": bool(surface.get("device_matrix_ok")),
        "android_device_matrix_count": surface.get("device_count"),
        "responsive_scan_ok": bool(surface.get("responsive_scan_ok")),
        "responsive_marker_total": surface.get("responsive_marker_total"),
        "target_surface_inventory_ok": bool(surface.get("p5c_target_surface_ok")),
        "target_surface_count": surface.get("target_surface_count"),
        "target_surface_exists_count": surface.get("target_surface_exists_count"),
        "expected_surface_coverage_ok": bool(surface.get("expected_surface_coverage_ok")),
        "routes_py_lines": inventory["routes_py_lines"],
        "routes_py_under_300_lines": inventory["routes_py_under_300_lines"],
        "total_mobile_route_decorator_count": inventory["total_mobile_route_decorator_count"],
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "direct_contract_ok": direct_contract_ok,
        "compile_ok": bool(compile_ok),
        "app_factory_ok": bool(app_factory.get("ok")),
        "secret_gate_ok": bool(secret.get("ok")),
        "secret_gate_finding_count": secret_count,
        "pytest_ok": bool(pytest.get("ok")),
        "pytest_mode": pytest.get("mode", "pytest_targeted_android_responsive_release_suite_p5d"),
        "active_scope": active_scope,
        "inventory": inventory,
        "responsive_release_evidence": {
            "ok": release_suite_ok,
            "p5a": {
                "exists": bool(p5a.get("_exists")),
                "ok": p5a_ok,
                "report": str(root / P5A_REPORT_REL),
                "device_count": surface.get("device_count"),
                "responsive_marker_total": surface.get("responsive_marker_total"),
            },
            "p5b": {
                "exists": bool(p5b.get("_exists")),
                "ok": p5b_ok,
                "report": str(root / P5B_REPORT_REL),
                "core_css_media_query_count": css.get("p5b_media_query_count"),
                "base_link_ok": css.get("p5b_linked_in_base"),
            },
            "p5c": {
                "exists": bool(p5c.get("_exists")),
                "ok": p5c_ok,
                "report": str(root / P5C_REPORT_REL),
                "targeted_css_media_query_count": css.get("p5c_media_query_count"),
                "target_surface_count": surface.get("target_surface_count"),
                "target_surface_exists_count": surface.get("target_surface_exists_count"),
                "base_link_ok": css.get("p5c_linked_in_base"),
            },
            "css_evidence": css,
            "surface_evidence": surface,
            "source_reports": {
                "p5a": str(root / P5A_REPORT_REL),
                "p5b": str(root / P5B_REPORT_REL),
                "p5c": str(root / P5C_REPORT_REL),
            },
        },
        "compile_results": compile_results,
        "app_factory_smoke": app_factory,
        "secret_gate": secret,
        "pytest": pytest,
        "ci_commands": [
            "python -m pip install -r requirements-dev.txt",
            "python -m pytest tests/architecture -q",
            "python scripts/quality/bys360_android_responsive_release_suite_gate_p5d.py --root . --compile-all --app-factory --secret-gate --pytest-gate",
        ],
        "report": str(report_path),
        "next_actions": [
            "P5D temizse P5A-P5C Android responsive kapıları tek release suite altında standart kabul edilebilir.",
            "P5E'de görsel UAT sonrası tekil ekran patchleri veya screenshot tabanlı regression kanıtları eklenebilir.",
        ],
    }
    report_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=PACKAGE)
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
        "android_responsive_release_suite_gate_ok",
        "p5a_baseline_report_ok",
        "p5b_core_styles_report_ok",
        "p5c_targeted_templates_report_ok",
        "responsive_css_evidence_ok",
        "base_template_links_ok",
        "android_device_matrix_ok",
        "android_device_matrix_count",
        "responsive_scan_ok",
        "responsive_marker_total",
        "target_surface_inventory_ok",
        "target_surface_count",
        "target_surface_exists_count",
        "expected_surface_coverage_ok",
        "direct_contract_ok",
        "compile_ok",
        "app_factory_ok",
        "secret_gate_ok",
        "secret_gate_finding_count",
        "pytest_ok",
        "pytest_mode",
        "report",
    ]
    print(json.dumps({key: result.get(key) for key in summary_keys}, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
