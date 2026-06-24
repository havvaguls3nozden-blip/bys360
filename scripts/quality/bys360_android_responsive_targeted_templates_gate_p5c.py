#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BYS360 P5C Android Responsive Targeted Templates Gate
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
from typing import Any, Dict, List

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P5C_ANDROID_RESPONSIVE_TARGETED_TEMPLATES_GATE"
REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_TARGETED_TEMPLATES_GATE_P5C_REPORT.json")
CSS_REL = Path("app/static/css/bys360_android_responsive_targeted_p5c.css")
BASE_REL = Path("app/templates/base.html")
P5B_REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_CORE_STYLES_GATE_P5B_REPORT.json")

TARGETED_LINK = "{{ url_for('static', filename='css/bys360_android_responsive_targeted_p5c.css') }}"
TARGETED_LINK_TAG = f'<link rel="stylesheet" href="{TARGETED_LINK}">'

TARGET_TEMPLATE_PATHS = [
    "app/templates/dashboard.html",
    "app/templates/home.html",
    "app/templates/evaluation_form.html",
    "app/templates/admin_ai_center.html",
    "app/templates/admin_ai_executive_brief.html",
    "app/templates/admin_ai_feedback.html",
    "app/templates/admin_ai_final_live_hardening.html",
    "app/templates/admin_ai_governance_hub.html",
    "app/templates/admin_ai_governance_settings.html",
    "app/templates/admin_ai_go_live_readiness.html",
    "app/templates/admin_ai_management_pack.html",
    "app/templates/admin_ai_module_health.html",
    "app/templates/admin_ai_notification_priority.html",
    "app/templates/admin_ai_operations_report.html",
    "app/templates/admin_ai_preflight.html",
    "app/templates/admin_ai_quality_hub.html",
    "app/templates/admin_ai_recommendations.html",
    "app/templates/admin_ai_redaction_rules.html",
    "app/templates/admin_ai_requests.html",
    "app/templates/admin_ai_schema_not_ready.html",
    "app/templates/admin_ai_smoke.html",
    "app/templates/admin_ai_weekly_summary.html",
    "app/templates/communication_suite_macros.html",
]

REQUIRED_CSS_MARKERS = [
    "P5C_ANDROID_RESPONSIVE_TARGETED",
    "p5c-dashboard",
    "p5c-home",
    "p5c-evaluation-form",
    "p5c-admin-ai",
    "p5c-wide-tables",
    "p5c-wide-forms",
    "p5c-landscape",
    "p5c-touch-targets",
    "p5c-safe-overflow",
    "p5c-bottom-nav-safe",
    "p5c-print-neutral",
]

CSS_CONTENT = """/* BYS360 P5C_ANDROID_RESPONSIVE_TARGETED */
/*
  Android responsive targeted layer.
  Scope: high-risk templates from P5B report: dashboard, home, evaluation_form,
  admin AI surfaces, wide forms/tables/cards, modal/sidebar and landscape.
  This stylesheet is additive and low-risk: it avoids changing brand colors.
*/

:root {
  --bys360-p5c-mobile-gap: clamp(10px, 3vw, 18px);
  --bys360-p5c-card-radius: 16px;
  --bys360-p5c-readable-width: min(100%, 1120px);
}

/* p5c-safe-overflow */
html,
body {
  max-width: 100%;
  overflow-x: hidden;
}

img,
svg,
canvas,
video,
iframe {
  max-width: 100%;
  height: auto;
}

pre,
code,
.bys360-code,
.log-output,
.json-output {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
}

/* p5c-wide-tables */
.table-responsive,
.responsive-table,
.bys360-table-wrap,
.table-container,
.table-scroll,
.data-table-wrap,
.table-card,
.table-panel,
.table,
table {
  max-width: 100%;
}

.table-responsive,
.responsive-table,
.bys360-table-wrap,
.table-container,
.table-scroll,
.data-table-wrap,
.table-card,
.table-panel {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

table {
  border-collapse: collapse;
}

td,
th {
  overflow-wrap: anywhere;
}

/* p5c-wide-forms */
form,
.form-grid,
.form-row,
.form-group,
.input-group,
.filter-bar,
.search-row,
.toolbar,
.action-row,
.actions,
.button-row {
  min-width: 0;
}

input,
select,
textarea,
button,
.btn,
.button,
.form-control,
.form-select {
  max-width: 100%;
}

textarea {
  resize: vertical;
}

/* p5c-touch-targets */
button,
.btn,
.button,
[role="button"],
input[type="button"],
input[type="submit"],
input[type="reset"],
.nav-link,
.dropdown-item,
.mobile-action {
  min-height: 44px;
  touch-action: manipulation;
}

/* p5c-dashboard */
.dashboard,
.dashboard-container,
.dashboard-grid,
.dashboard-cards,
.metric-grid,
.stats-grid,
.kpi-grid,
.home-grid,
.widget-grid {
  min-width: 0;
}

.dashboard-card,
.metric-card,
.kpi-card,
.widget-card,
.stat-card,
.card,
.panel {
  min-width: 0;
  overflow-wrap: anywhere;
}

/* p5c-home */
.home,
.home-page,
.home-hero,
.welcome-panel,
.quick-actions,
.shortcut-grid {
  max-width: 100%;
  min-width: 0;
}

/* p5c-evaluation-form */
.evaluation-form,
.evaluation-card,
.criteria-list,
.criteria-item,
.score-form,
.performance-form,
.rating-grid,
.score-grid {
  min-width: 0;
  max-width: 100%;
}

/* p5c-admin-ai */
.admin-ai,
.ai-admin,
.ai-panel,
.ai-card,
.ai-grid,
.ai-center,
.ai-governance,
.ai-report,
.ai-quality,
.ai-preflight,
.ai-recommendation,
.ai-operations {
  min-width: 0;
  max-width: 100%;
  overflow-wrap: anywhere;
}

@media (max-width: 768px) {
  body {
    min-width: 0;
  }

  main,
  .main,
  .main-content,
  .content,
  .content-wrapper,
  .page-content,
  .container,
  .container-fluid,
  .admin-container,
  .page-shell,
  .bys360-shell,
  .bys360-page {
    width: 100% !important;
    max-width: 100% !important;
    padding-left: var(--bys360-p5c-mobile-gap) !important;
    padding-right: var(--bys360-p5c-mobile-gap) !important;
    box-sizing: border-box;
  }

  .row,
  .grid,
  .dashboard-grid,
  .dashboard-cards,
  .metric-grid,
  .stats-grid,
  .kpi-grid,
  .home-grid,
  .widget-grid,
  .quick-actions,
  .form-grid,
  .filter-grid,
  .ai-grid,
  .cards-grid {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: var(--bys360-p5c-mobile-gap) !important;
  }

  .col,
  [class*="col-"],
  .card,
  .panel,
  .dashboard-card,
  .metric-card,
  .kpi-card,
  .widget-card,
  .ai-card {
    width: 100% !important;
    max-width: 100% !important;
    flex: 0 0 auto !important;
  }

  .toolbar,
  .filter-bar,
  .search-row,
  .action-row,
  .actions,
  .button-row,
  .form-actions,
  .modal-footer {
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 10px !important;
  }

  .toolbar > *,
  .filter-bar > *,
  .search-row > *,
  .action-row > *,
  .actions > *,
  .button-row > *,
  .form-actions > *,
  .modal-footer > * {
    width: 100% !important;
    max-width: 100% !important;
  }

  .btn,
  .button,
  button,
  input[type="submit"],
  input[type="button"] {
    width: 100%;
    justify-content: center;
  }

  .modal-dialog,
  .modal-content,
  .dialog,
  .drawer,
  .sidebar-panel,
  .offcanvas {
    max-width: calc(100vw - 20px) !important;
    width: calc(100vw - 20px) !important;
    margin-left: auto !important;
    margin-right: auto !important;
  }

  h1,
  .page-title {
    font-size: clamp(1.25rem, 5vw, 1.75rem) !important;
    line-height: 1.2;
  }

  h2,
  .section-title {
    font-size: clamp(1.1rem, 4.4vw, 1.45rem) !important;
  }
}

@media (max-width: 480px) {
  .card,
  .panel,
  .dashboard-card,
  .metric-card,
  .kpi-card,
  .widget-card,
  .ai-card,
  .evaluation-card {
    border-radius: var(--bys360-p5c-card-radius);
    padding: clamp(12px, 4vw, 18px) !important;
  }

  .table,
  table {
    font-size: 0.92rem;
  }

  td,
  th {
    padding: 0.55rem 0.65rem;
  }

  .hide-on-android-small,
  .desktop-only {
    display: none !important;
  }

  .show-on-android-small,
  .mobile-only {
    display: initial !important;
  }
}

@media (min-width: 481px) and (max-width: 768px) {
  .tablet-two-col,
  .responsive-two-col {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: var(--bys360-p5c-mobile-gap) !important;
  }
}

/* p5c-landscape */
@media (orientation: landscape) and (max-height: 520px) {
  .page-header,
  .hero,
  .home-hero,
  .dashboard-header {
    padding-top: 10px !important;
    padding-bottom: 10px !important;
  }

  .modal-dialog,
  .offcanvas,
  .sidebar-panel {
    max-height: calc(100vh - 16px) !important;
    overflow-y: auto !important;
  }
}

/* p5c-bottom-nav-safe */
@media (max-width: 768px) {
  .bottom-nav,
  .mobile-bottom-nav,
  .app-bottom-nav,
  .fixed-bottom {
    padding-bottom: max(8px, env(safe-area-inset-bottom));
  }

  body.has-bottom-nav,
  .has-mobile-bottom-nav main,
  .has-mobile-bottom-nav .main-content {
    padding-bottom: calc(72px + env(safe-area-inset-bottom)) !important;
  }
}

/* p5c-print-neutral */
@media print {
  .bottom-nav,
  .mobile-bottom-nav,
  .app-bottom-nav,
  .sidebar,
  .offcanvas {
    display: none !important;
  }

  body {
    overflow: visible !important;
  }
}
"""


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(read_text(path))
    except Exception:
        return {}


def route_decorator_inventory(root: Path) -> Dict[str, Any]:
    mobile_dir = root / "app/api/mobile"
    domains_dir = mobile_dir / "domains"
    paths = [mobile_dir / "routes.py"]
    if domains_dir.exists():
        paths.extend(sorted(domains_dir.glob("*.py")))
    domain_inventory = []
    total = 0
    route_pat = re.compile(r"@\w+\.(route|get|post|put|patch|delete)\(")
    duplicate_keys = []
    seen = set()
    for path in paths:
        rel = path.relative_to(root).as_posix() if path.exists() else str(path)
        text = read_text(path) if path.exists() else ""
        hits = route_pat.findall(text)
        total += len(hits)
        for line in text.splitlines():
            stripped = line.strip()
            if "@mobile_bp." in stripped and "(" in stripped:
                if stripped in seen:
                    duplicate_keys.append(stripped)
                seen.add(stripped)
        domain_inventory.append({
            "path": rel,
            "exists": path.exists(),
            "route_count": len(hits),
            "lines": len(text.splitlines()) if text else 0,
        })
    routes_py = root / "app/api/mobile/routes.py"
    routes_text = read_text(routes_py) if routes_py.exists() else ""
    return {
        "routes_py_lines": len(routes_text.splitlines()) if routes_text else 0,
        "routes_py_under_300_lines": (len(routes_text.splitlines()) <= 300) if routes_text else False,
        "routes_py_route_count": domain_inventory[0]["route_count"] if domain_inventory else 0,
        "domains_dir_exists": domains_dir.exists(),
        "domain_inventory": domain_inventory,
        "total_mobile_route_decorator_count": total,
        "expected_contract_route_count": 24,
        "route_contract_count_expected": total == 24,
        "duplicate_route_decorators": duplicate_keys,
    }


def ensure_css(root: Path) -> Dict[str, Any]:
    css_path = root / CSS_REL
    old = read_text(css_path) if css_path.exists() else ""
    changed = old != CSS_CONTENT
    if changed:
        write_text(css_path, CSS_CONTENT)
    text = read_text(css_path)
    missing = [m for m in REQUIRED_CSS_MARKERS if m not in text]
    return {
        "path": CSS_REL.as_posix(),
        "exists": css_path.exists(),
        "changed": changed,
        "line_count": len(text.splitlines()),
        "byte_count": len(text.encode("utf-8")),
        "required_marker_count": len(REQUIRED_CSS_MARKERS),
        "required_marker_total": len(REQUIRED_CSS_MARKERS) - len(missing),
        "missing_required_markers": missing,
        "media_query_count": text.count("@media"),
        "ok": css_path.exists() and not missing and text.count("@media") >= 5,
    }


def ensure_base_link(root: Path) -> Dict[str, Any]:
    base_path = root / BASE_REL
    if not base_path.exists():
        return {"path": BASE_REL.as_posix(), "exists": False, "changed": False, "linked": False, "ok": False, "error": "base.html not found"}
    text = read_text(base_path)
    if TARGETED_LINK in text:
        return {"path": BASE_REL.as_posix(), "exists": True, "changed": False, "linked": True, "ok": True, "error": ""}
    p5b_link_re = re.compile(r'(?P<link><link[^>]+bys360_android_responsive_core_p5b\.css[^>]*>\s*)')
    m = p5b_link_re.search(text)
    if m:
        text = text[:m.end()] + "\n    " + TARGETED_LINK_TAG + text[m.end():]
    elif "</head>" in text:
        text = text.replace("</head>", f"    {TARGETED_LINK_TAG}\n</head>", 1)
    else:
        text = text + "\n" + TARGETED_LINK_TAG + "\n"
    write_text(base_path, text)
    new_text = read_text(base_path)
    linked = TARGETED_LINK in new_text
    return {"path": BASE_REL.as_posix(), "exists": True, "changed": True, "linked": linked, "ok": linked, "error": ""}


def target_surface_report(root: Path, p5b_report: Dict[str, Any]) -> Dict[str, Any]:
    p5b_priority = p5b_report.get("surface_priority", {}).get("priority_no_marker_sample") or []
    target_paths = list(dict.fromkeys(p5b_priority + TARGET_TEMPLATE_PATHS))
    items = []
    exists_count = 0
    for rel in target_paths:
        path = root / rel
        exists = path.exists()
        if exists:
            exists_count += 1
            text = read_text(path)
            markers = [marker for marker in ["@media", "max-width", "min-width", "viewport", "matchMedia", "table", "form"] if marker in text]
            items.append({"path": rel, "exists": True, "line_count": len(text.splitlines()), "responsive_marker_hits": markers})
        else:
            items.append({"path": rel, "exists": False, "line_count": 0, "responsive_marker_hits": []})
    high_value = ["app/templates/dashboard.html", "app/templates/home.html", "app/templates/evaluation_form.html"]
    high_value_present = all((root / x).exists() for x in high_value)
    return {
        "source_priority_count": len(p5b_priority),
        "target_surface_count": len(target_paths),
        "target_surface_exists_count": exists_count,
        "high_value_templates_present": high_value_present,
        "targeted_templates": items[:80],
        "ok": exists_count >= 3 and high_value_present,
        "note": "P5C applies a central targeted stylesheet to these surfaces. Individual template patches can follow after visual UAT.",
    }


def ensure_active_scope_marker(root: Path) -> Dict[str, Any]:
    conftest = root / "tests/architecture/conftest.py"
    marker = "BYS360_ACTIVE_ARCHITECTURE_TEST_P5C_ANDROID_RESPONSIVE_TARGETED_TEMPLATES"
    if not conftest.exists():
        return {"path": str(conftest), "changed": False, "reason": "missing_conftest", "compile_ok": False, "compile_error": "missing conftest.py"}
    text = read_text(conftest)
    if marker in text:
        changed = False
        reason = "already_present"
    else:
        text = text.rstrip() + f"\n\n# {marker}: test_android_responsive_targeted_templates_p5c.py\n"
        write_text(conftest, text)
        changed = True
        reason = "appended_safe_marker"
    try:
        py_compile.compile(str(conftest), doraise=True)
        return {"path": str(conftest), "changed": changed, "reason": reason, "compile_ok": True, "compile_error": ""}
    except Exception as exc:
        return {"path": str(conftest), "changed": changed, "reason": reason, "compile_ok": False, "compile_error": str(exc)}


def compile_files(root: Path) -> List[Dict[str, Any]]:
    rels = [
        Path("scripts/quality/bys360_android_responsive_targeted_templates_gate_p5c.py"),
        Path("tests/architecture/test_android_responsive_targeted_templates_p5c.py"),
        Path("tests/architecture/conftest.py"),
    ]
    results = []
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
    return results


def run_cmd(cmd: List[str], cwd: Path, env: Dict[str, str] | None = None, timeout: int = 90) -> Dict[str, Any]:
    try:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        proc = subprocess.run(cmd, cwd=str(cwd), env=merged_env, text=True, capture_output=True, timeout=timeout)
        return {"returncode": proc.returncode, "stdout_tail": proc.stdout[-1200:], "stderr_tail": proc.stderr[-1200:], "ok": proc.returncode == 0, "cmd": cmd}
    except Exception as exc:
        return {"returncode": -1, "stdout_tail": "", "stderr_tail": str(exc), "ok": False, "cmd": cmd}


def app_factory_smoke(root: Path, python_exe: str) -> Dict[str, Any]:
    env = {"FLASK_ENV": "testing", "APP_ENV": "testing", "DATABASE_URL": "sqlite:///:memory:", "BYS360_TESTING": "1"}
    return run_cmd([python_exe, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], root, env=env, timeout=120)


def secret_gate(root: Path, python_exe: str) -> Dict[str, Any]:
    gate = root / "scripts/quality/bys360_secret_repo_gate.py"
    if not gate.exists():
        return {"ok": True, "skipped": True, "reason": "secret gate script not found", "parsed": {"finding_count": 0}}
    result = run_cmd([python_exe, str(gate), "--root", str(root)], root, timeout=120)
    parsed = {}
    try:
        match = re.search(r"\{[\s\S]*\}", result.get("stdout_tail", ""))
        if match:
            parsed = json.loads(match.group(0))
    except Exception:
        parsed = {}
    result["parsed"] = parsed
    result["ok"] = result["ok"] and parsed.get("ok", result["ok"]) is True
    return result


def pytest_gate(root: Path, python_exe: str) -> Dict[str, Any]:
    return run_cmd([python_exe, "-m", "pytest", "tests\\architecture\\test_android_responsive_targeted_templates_p5c.py", "-q"], root, timeout=120)


def run_gate(root: Path, args: argparse.Namespace) -> Dict[str, Any]:
    report_path = root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)

    active_scope = ensure_active_scope_marker(root)
    p5b_report = read_json(root / P5B_REPORT_REL)
    css = ensure_css(root)
    base_link = ensure_base_link(root)
    surfaces = target_surface_report(root, p5b_report)
    inventory = route_decorator_inventory(root)
    p5b_ok = bool(p5b_report.get("ok") and p5b_report.get("android_responsive_core_styles_gate_ok"))

    compile_results = compile_files(root) if args.compile_all else []
    compile_ok = all(x["ok"] for x in compile_results) if compile_results else True
    if not active_scope.get("compile_ok", False):
        compile_ok = False

    python_exe = sys.executable
    app_smoke = app_factory_smoke(root, python_exe) if args.app_factory else {"ok": True, "skipped": True}
    sec_gate = secret_gate(root, python_exe) if args.secret_gate else {"ok": True, "parsed": {"finding_count": 0}, "skipped": True}
    pytest = pytest_gate(root, python_exe) if args.pytest_gate else {"ok": True, "skipped": True}
    secret_findings = int(sec_gate.get("parsed", {}).get("finding_count", 0) or 0)

    targeted_gate_ok = bool(p5b_ok and css.get("ok") and base_link.get("ok") and surfaces.get("ok") and inventory.get("routes_py_under_300_lines") and inventory.get("route_contract_count_expected"))
    ok = bool(targeted_gate_ok and compile_ok and app_smoke.get("ok") and sec_gate.get("ok") and secret_findings == 0 and pytest.get("ok"))

    report: Dict[str, Any] = {
        "ok": ok,
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "android_responsive_targeted_templates_gate_ok": targeted_gate_ok,
        "targeted_responsive_css_ok": css.get("ok"),
        "base_template_link_ok": base_link.get("ok"),
        "p5b_core_styles_report_ok": p5b_ok,
        "target_surface_inventory_ok": surfaces.get("ok"),
        "routes_py_lines": inventory.get("routes_py_lines"),
        "routes_py_under_300_lines": inventory.get("routes_py_under_300_lines"),
        "total_mobile_route_decorator_count": inventory.get("total_mobile_route_decorator_count"),
        "expected_contract_route_count": inventory.get("expected_contract_route_count"),
        "direct_contract_ok": bool(inventory.get("route_contract_count_expected")),
        "core_css_media_query_count": css.get("media_query_count"),
        "targeted_css_required_marker_total": css.get("required_marker_total"),
        "target_surface_count": surfaces.get("target_surface_count"),
        "target_surface_exists_count": surfaces.get("target_surface_exists_count"),
        "compile_ok": compile_ok,
        "app_factory_ok": bool(app_smoke.get("ok")),
        "secret_gate_ok": bool(sec_gate.get("ok")),
        "secret_gate_finding_count": secret_findings,
        "pytest_ok": bool(pytest.get("ok")),
        "pytest_mode": "pytest_targeted_android_responsive_targeted_templates_p5c",
        "active_scope": active_scope,
        "inventory": inventory,
        "targeted_css": css,
        "base_template_link": base_link,
        "target_surfaces": surfaces,
        "compile_results": compile_results,
        "app_factory_smoke": app_smoke,
        "secret_gate": sec_gate,
        "pytest": pytest,
        "source_reports": {"p5b": str(root / P5B_REPORT_REL)},
        "ci_commands": [
            "python -m pip install -r requirements-dev.txt",
            "python -m pytest tests/architecture -q",
            "python scripts/quality/bys360_android_responsive_targeted_templates_gate_p5c.py --root . --compile-all --app-factory --secret-gate --pytest-gate",
        ],
        "report": str(report_path),
        "next_actions": [
            "P5C temizse dashboard/home/evaluation_form/admin AI gibi yüksek riskli yüzeyler merkezi hedefli responsive katmanla güçlendirilmiş kabul edilebilir.",
            "P5D'de responsive release suite altında P5A-P5C raporları tek runner ile birleştirilebilir.",
        ],
    }
    write_text(report_path, json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--app-factory", action="store_true")
    parser.add_argument("--secret-gate", action="store_true")
    parser.add_argument("--pytest-gate", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    report = run_gate(root, args)
    print(json.dumps({
        "ok": report["ok"],
        "package": report["package"],
        "android_responsive_targeted_templates_gate_ok": report["android_responsive_targeted_templates_gate_ok"],
        "targeted_responsive_css_ok": report["targeted_responsive_css_ok"],
        "base_template_link_ok": report["base_template_link_ok"],
        "p5b_core_styles_report_ok": report["p5b_core_styles_report_ok"],
        "target_surface_inventory_ok": report["target_surface_inventory_ok"],
        "target_surface_count": report["target_surface_count"],
        "target_surface_exists_count": report["target_surface_exists_count"],
        "routes_py_lines": report["routes_py_lines"],
        "total_mobile_route_decorator_count": report["total_mobile_route_decorator_count"],
        "direct_contract_ok": report["direct_contract_ok"],
        "compile_ok": report["compile_ok"],
        "app_factory_ok": report["app_factory_ok"],
        "secret_gate_ok": report["secret_gate_ok"],
        "secret_gate_finding_count": report["secret_gate_finding_count"],
        "pytest_ok": report["pytest_ok"],
        "pytest_mode": report["pytest_mode"],
        "report": report["report"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
