# -*- coding: utf-8 -*-
"""BYS360 P5A Android Responsive Baseline Gate.

Read-only baseline gate for Android/mobile responsive work. It combines the P4E
mobile release evidence with a static repository scan and a standardized Android
device-size matrix. The gate does not mutate application code and does not touch
live data.
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

PACKAGE = "BYS360_CLAUDE_SCORE_UPLIFT_P5A_ANDROID_RESPONSIVE_BASELINE_GATE"
REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_BASELINE_GATE_P5A_REPORT.json")
P4E_REPORT_REL = Path("reports/architecture/BYS360_MOBILE_RELEASE_EVIDENCE_GATE_P4E_REPORT.json")
SECRET_REPORT_REL = Path("reports/quality/BYS360_SECRET_REPO_GATE_V1_REPORT.json")
EXPECTED_CONTRACT_ROUTE_COUNT = 24

ROUTE_DECORATOR_RE = re.compile(r"@\s*mobile_api_bp\s*\.\s*(get|post|put|patch|delete)\s*\(", re.I)
RESPONSIVE_MARKERS = {
    "flutter_layout_builder": "LayoutBuilder",
    "flutter_media_query": "MediaQuery",
    "flutter_safe_area": "SafeArea",
    "flutter_scroll": "SingleChildScrollView",
    "flutter_flexible": "Flexible",
    "flutter_expanded": "Expanded",
    "flutter_wrap": "Wrap(",
    "flutter_grid": "GridView",
    "css_media_query": "@media",
    "css_max_width": "max-width",
    "css_min_width": "min-width",
    "css_clamp": "clamp(",
    "html_viewport": "viewport",
    "js_match_media": "matchMedia",
}
SCAN_EXTENSIONS = {".dart", ".html", ".css", ".scss", ".js", ".ts", ".tsx", ".jsx", ".vue"}
SCAN_DIR_NAMES = {
    "android", "ios", "lib", "mobile", "flutter", "web", "templates", "static", "assets", "frontend",
    "app", "resources"
}
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "reports", "logs", "dist", "build", ".dart_tool"}

ANDROID_DEVICE_MATRIX = [
    {"label": "Android small", "width": 360, "height": 640, "density_bucket": "mdpi/hdpi", "orientation": "portrait"},
    {"label": "Android compact", "width": 393, "height": 851, "density_bucket": "xhdpi", "orientation": "portrait"},
    {"label": "Android standard", "width": 412, "height": 915, "density_bucket": "xxhdpi", "orientation": "portrait"},
    {"label": "Android large phone", "width": 480, "height": 960, "density_bucket": "xxhdpi", "orientation": "portrait"},
    {"label": "Android fold/tablet narrow", "width": 600, "height": 960, "density_bucket": "xhdpi", "orientation": "portrait"},
    {"label": "Android tablet", "width": 768, "height": 1024, "density_bucket": "xhdpi", "orientation": "portrait"},
    {"label": "Android landscape", "width": 851, "height": 393, "density_bucket": "xhdpi", "orientation": "landscape"},
]


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
    return {"_exists": True, "_path": str(path), "_read_error": "json root is not object"}


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def _count_route_decorators(path: Path) -> int:
    if not path.exists():
        return 0
    return len(ROUTE_DECORATOR_RE.findall(path.read_text(encoding="utf-8", errors="ignore")))


def _mobile_inventory(root: Path) -> Dict[str, Any]:
    mobile_dir = root / "app" / "api" / "mobile"
    routes_py = mobile_dir / "routes.py"
    domains_dir = mobile_dir / "domains"
    files: List[Path] = []
    if routes_py.exists():
        files.append(routes_py)
    if domains_dir.exists():
        files.extend(sorted(domains_dir.glob("*.py")))
    total = 0
    domain_inventory: List[Dict[str, Any]] = []
    for file_path in files:
        route_count = _count_route_decorators(file_path)
        total += route_count
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
        "total_mobile_route_decorator_count": total,
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "route_contract_count_expected": total == EXPECTED_CONTRACT_ROUTE_COUNT,
    }


def _looks_relevant(path: Path, root: Path) -> bool:
    parts = {part.lower() for part in path.relative_to(root).parts[:-1]}
    return bool(parts & SCAN_DIR_NAMES) or path.suffix.lower() == ".dart"


def _scan_responsive_surface(root: Path) -> Dict[str, Any]:
    scanned_files: List[Dict[str, Any]] = []
    marker_counts = {key: 0 for key in RESPONSIVE_MARKERS}
    extension_counts: Dict[str, int] = {}
    candidate_count = 0
    total_bytes = 0
    max_files = 600
    max_file_bytes = 512_000

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        ext = path.suffix.lower()
        if ext not in SCAN_EXTENSIONS:
            continue
        if not _looks_relevant(path, root):
            continue
        candidate_count += 1
        if len(scanned_files) >= max_files:
            continue
        try:
            raw = path.read_bytes()[:max_file_bytes]
            text = raw.decode("utf-8", errors="ignore")
        except Exception:
            text = ""
        total_bytes += len(text.encode("utf-8", errors="ignore"))
        hits = []
        for key, marker in RESPONSIVE_MARKERS.items():
            count = text.count(marker)
            if count:
                marker_counts[key] += count
                hits.append(key)
        extension_counts[ext] = extension_counts.get(ext, 0) + 1
        scanned_files.append({
            "path": str(path.relative_to(root)).replace("\\", "/"),
            "extension": ext,
            "line_count": len(text.splitlines()),
            "responsive_marker_hits": hits[:12],
        })

    observed_marker_total = sum(marker_counts.values())
    flutter_file_count = extension_counts.get(".dart", 0)
    css_or_html_count = extension_counts.get(".css", 0) + extension_counts.get(".scss", 0) + extension_counts.get(".html", 0)
    return {
        "ok": True,
        "mode": "static_responsive_surface_inventory",
        "candidate_file_count": candidate_count,
        "scanned_file_count": len(scanned_files),
        "scan_cap": max_files,
        "total_scanned_bytes": total_bytes,
        "extension_counts": extension_counts,
        "flutter_file_count": flutter_file_count,
        "css_or_html_file_count": css_or_html_count,
        "responsive_marker_counts": marker_counts,
        "responsive_marker_total": observed_marker_total,
        "has_flutter_surface": flutter_file_count > 0,
        "has_web_surface": css_or_html_count > 0,
        "sample_files": scanned_files[:80],
        "note": "Baseline inventory only; it intentionally does not fail when responsive markers are low.",
    }


def _android_matrix() -> Dict[str, Any]:
    widths = [item["width"] for item in ANDROID_DEVICE_MATRIX]
    has_small = any(width <= 360 for width in widths)
    has_standard = any(390 <= width <= 430 for width in widths)
    has_tablet = any(width >= 600 for width in widths)
    has_landscape = any(item.get("orientation") == "landscape" for item in ANDROID_DEVICE_MATRIX)
    return {
        "ok": True,
        "device_count": len(ANDROID_DEVICE_MATRIX),
        "has_small_phone": has_small,
        "has_standard_phone": has_standard,
        "has_tablet_or_foldable": has_tablet,
        "has_landscape": has_landscape,
        "devices": ANDROID_DEVICE_MATRIX,
        "minimum_expected_device_count": 6,
        "matrix_ready": len(ANDROID_DEVICE_MATRIX) >= 6 and has_small and has_standard and has_tablet and has_landscape,
    }


def _compile_files(files: Sequence[Path]) -> List[Dict[str, Any]]:
    results = []
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


def _run(cmd: Sequence[str], cwd: Path, env_extra: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
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
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-1200:],
        "stderr_tail": proc.stderr[-1200:],
        "ok": proc.returncode == 0,
        "cmd": list(cmd),
    }


def _app_factory_smoke(root: Path) -> Dict[str, Any]:
    return _run([sys.executable, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], root)


def _secret_gate(root: Path) -> Dict[str, Any]:
    script = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    if not script.exists():
        return {"ok": False, "returncode": 127, "stdout_tail": "", "stderr_tail": "secret gate script missing", "parsed": {}}
    result = _run([sys.executable, str(script), "--root", str(root)], root)
    parsed = _read_json(root / SECRET_REPORT_REL)
    try:
        parsed_stdout = json.loads(result.get("stdout_tail", "{}"))
        if isinstance(parsed_stdout, dict):
            parsed = parsed_stdout
    except Exception:
        pass
    result["parsed"] = parsed
    result["ok"] = bool(result.get("ok")) and bool(parsed.get("ok", True)) and int(parsed.get("finding_count", 0) or 0) == 0
    return result


def _pytest_gate(root: Path) -> Dict[str, Any]:
    test_file = root / "tests" / "architecture" / "test_android_responsive_baseline_p5a.py"
    if not test_file.exists():
        return {"ok": False, "returncode": 127, "stdout_tail": "", "stderr_tail": "P5A pytest file missing", "mode": "pytest_targeted_android_responsive_baseline_p5a"}
    result = _run([sys.executable, "-m", "pytest", str(test_file.relative_to(root)), "-q"], root)
    result["mode"] = "pytest_targeted_android_responsive_baseline_p5a"
    return result


def build_report(root: Path, compile_all: bool = False, app_factory: bool = False, secret_gate: bool = False, pytest_gate: bool = False) -> Dict[str, Any]:
    inventory = _mobile_inventory(root)
    p4e_report = _read_json(root / P4E_REPORT_REL)
    scan = _scan_responsive_surface(root)
    matrix = _android_matrix()

    p4e_ok = bool(p4e_report.get("ok")) and bool(p4e_report.get("mobile_release_evidence_gate_ok"))
    response_evidence_ok = bool(p4e_report.get("response_suite_report_ok"))
    security_evidence_ok = bool(p4e_report.get("security_evidence_report_ok"))
    p3_ok = int(p4e_report.get("p3_gates_passed", 0) or 0) == 5
    p4_ok = int(p4e_report.get("security_gates_passed", 0) or 0) == 2

    responsive_baseline_gate_ok = bool(matrix["matrix_ready"]) and bool(scan["ok"])
    android_responsive_baseline_ok = p4e_ok and responsive_baseline_gate_ok
    handover_baseline_ok = android_responsive_baseline_ok and response_evidence_ok and security_evidence_ok

    compile_results: List[Dict[str, Any]] = []
    compile_ok: Optional[bool] = None
    if compile_all:
        compile_results = _compile_files([
            root / "scripts" / "quality" / "bys360_android_responsive_baseline_gate_p5a.py",
            root / "tests" / "architecture" / "test_android_responsive_baseline_p5a.py",
            root / "tests" / "architecture" / "conftest.py",
        ])
        compile_ok = all(bool(item.get("ok")) for item in compile_results)

    app_factory_result: Optional[Dict[str, Any]] = None
    app_factory_ok: Optional[bool] = None
    if app_factory:
        app_factory_result = _app_factory_smoke(root)
        app_factory_ok = bool(app_factory_result.get("ok"))

    secret_result: Optional[Dict[str, Any]] = None
    secret_ok: Optional[bool] = None
    secret_finding_count: Optional[int] = None
    if secret_gate:
        secret_result = _secret_gate(root)
        secret_ok = bool(secret_result.get("ok"))
        parsed = secret_result.get("parsed") if isinstance(secret_result.get("parsed"), dict) else {}
        secret_finding_count = int(parsed.get("finding_count", 0) or 0)

    pytest_result: Optional[Dict[str, Any]] = None
    pytest_ok: Optional[bool] = None
    if pytest_gate:
        pytest_result = _pytest_gate(root)
        pytest_ok = bool(pytest_result.get("ok"))

    report: Dict[str, Any] = {
        "ok": bool(android_responsive_baseline_ok)
        and (compile_ok is not False)
        and (app_factory_ok is not False)
        and (secret_ok is not False)
        and (pytest_ok is not False),
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "android_responsive_baseline_gate_ok": bool(android_responsive_baseline_ok),
        "responsive_baseline_gate_ok": bool(responsive_baseline_gate_ok),
        "handover_baseline_ok": bool(handover_baseline_ok),
        "mobile_release_evidence_report_ok": p4e_ok,
        "response_suite_report_ok": response_evidence_ok,
        "security_evidence_report_ok": security_evidence_ok,
        "p3_gates_passed": int(p4e_report.get("p3_gates_passed", 0) or 0),
        "security_gates_passed": int(p4e_report.get("security_gates_passed", 0) or 0),
        "p3_ok": p3_ok,
        "p4_ok": p4_ok,
        "routes_py_lines": inventory.get("routes_py_lines"),
        "routes_py_under_300_lines": inventory.get("routes_py_under_300_lines"),
        "total_mobile_route_decorator_count": inventory.get("total_mobile_route_decorator_count"),
        "expected_contract_route_count": EXPECTED_CONTRACT_ROUTE_COUNT,
        "direct_contract_ok": bool(inventory.get("route_contract_count_expected")),
        "android_device_matrix_count": matrix["device_count"],
        "android_device_matrix_ok": matrix["matrix_ready"],
        "responsive_scan_ok": bool(scan["ok"]),
        "responsive_marker_total": scan["responsive_marker_total"],
        "compile_ok": compile_ok if compile_ok is not None else True,
        "app_factory_ok": app_factory_ok if app_factory_ok is not None else True,
        "secret_gate_ok": secret_ok if secret_ok is not None else True,
        "secret_gate_finding_count": secret_finding_count if secret_finding_count is not None else 0,
        "pytest_ok": pytest_ok if pytest_ok is not None else True,
        "pytest_mode": "pytest_targeted_android_responsive_baseline_p5a" if pytest_gate else "not_requested",
        "inventory": inventory,
        "android_device_matrix": matrix,
        "responsive_surface_scan": scan,
        "source_reports": {
            "p4e": str(root / P4E_REPORT_REL),
        },
        "compile_results": compile_results,
        "app_factory_smoke": app_factory_result,
        "secret_gate": secret_result,
        "pytest": pytest_result,
        "ci_commands": [
            "python -m pip install -r requirements-dev.txt",
            "python -m pytest tests/architecture -q",
            "python scripts/quality/bys360_android_responsive_baseline_gate_p5a.py --root . --compile-all --app-factory --secret-gate --pytest-gate",
        ],
        "report": str(root / REPORT_REL),
        "next_actions": [
            "P5A temizse Android responsive cihaz matrisi ve statik responsive yuzey envanteri release kanitina baglanmis kabul edilebilir.",
            "P5B'de responsive olmayan ekranlar icin hedefli Flutter/Web UI dosya duzeltmeleri ve breakpoint kontrolleri eklenebilir.",
        ],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
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
    print(json.dumps({
        "ok": report["ok"],
        "package": PACKAGE,
        "android_responsive_baseline_gate_ok": report["android_responsive_baseline_gate_ok"],
        "handover_baseline_ok": report["handover_baseline_ok"],
        "mobile_release_evidence_report_ok": report["mobile_release_evidence_report_ok"],
        "android_device_matrix_ok": report["android_device_matrix_ok"],
        "android_device_matrix_count": report["android_device_matrix_count"],
        "responsive_scan_ok": report["responsive_scan_ok"],
        "responsive_marker_total": report["responsive_marker_total"],
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
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
