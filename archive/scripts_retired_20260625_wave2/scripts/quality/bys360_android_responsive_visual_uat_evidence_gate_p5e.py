# -*- coding: utf-8 -*-
"""BYS360 P5E Android Responsive Visual UAT Evidence Gate.

This gate turns the P5D Android responsive release suite into a practical
visual-UAT/handover evidence package. It is safe: it reads existing reports,
creates a reusable checklist document, validates device/surface coverage, and
does not open browsers or touch live data.
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

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P5E_ANDROID_RESPONSIVE_VISUAL_UAT_EVIDENCE_GATE"
REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_VISUAL_UAT_EVIDENCE_GATE_P5E_REPORT.json")
P5D_REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_RELEASE_SUITE_GATE_P5D_V2_REPORT.json")
SECRET_REPORT_REL = Path("reports/quality/BYS360_SECRET_REPO_GATE_V1_REPORT.json")
CHECKLIST_REL = Path("docs/qa/BYS360_ANDROID_RESPONSIVE_VISUAL_UAT_CHECKLIST_P5E.md")
OPTIONAL_SCREENSHOT_DIR_REL = Path("reports/visual/android_responsive_p5e/screenshots")
EXPECTED_CONTRACT_ROUTE_COUNT = 24
MIN_ANDROID_DEVICE_COUNT = 7
MIN_TARGET_SURFACE_COUNT = 24
MIN_RESPONSIVE_MARKER_TOTAL = 1000
EXPECTED_SURFACES = [
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
    marker = "BYS360_ACTIVE_ARCHITECTURE_TEST_P5E_ANDROID_RESPONSIVE_VISUAL_UAT_EVIDENCE"
    if not conftest.exists():
        return {"path": str(conftest), "changed": False, "reason": "missing_conftest", "compile_ok": False, "compile_error": "missing conftest.py"}
    text = _read_text(conftest)
    if marker in text:
        changed = False
        reason = "already_present"
    else:
        text = text.rstrip() + f"\n\n# {marker}: test_android_responsive_visual_uat_evidence_p5e.py\n"
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
    test_file = root / "tests" / "architecture" / "test_android_responsive_visual_uat_evidence_p5e.py"
    if not test_file.exists():
        return {"ok": False, "returncode": 127, "stdout_tail": "", "stderr_tail": "P5E pytest file missing", "mode": "pytest_targeted_android_responsive_visual_uat_evidence_p5e"}
    result = _run([sys.executable, "-m", "pytest", str(test_file.relative_to(root)), "-q"], root)
    result["mode"] = "pytest_targeted_android_responsive_visual_uat_evidence_p5e"
    return result


def _collect_screenshot_evidence(root: Path) -> Dict[str, Any]:
    screenshot_dir = root / OPTIONAL_SCREENSHOT_DIR_REL
    image_exts = {".png", ".jpg", ".jpeg", ".webp"}
    screenshots = []
    if screenshot_dir.exists():
        for path in sorted(screenshot_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in image_exts:
                screenshots.append(str(path.relative_to(root)).replace("\\", "/"))
    return {
        "optional": True,
        "path": str(screenshot_dir),
        "exists": screenshot_dir.exists(),
        "screenshot_count": len(screenshots),
        "screenshots": screenshots[:50],
        "note": "Screenshot evidence is optional in P5E; manual visual UAT checklist is the required evidence artifact.",
    }


def _build_visual_uat_plan(p5d: Dict[str, Any]) -> Dict[str, Any]:
    evidence = p5d.get("responsive_release_evidence") if isinstance(p5d.get("responsive_release_evidence"), dict) else {}
    surface = evidence.get("surface_evidence") if isinstance(evidence.get("surface_evidence"), dict) else {}
    device_matrix = surface.get("p5a_device_matrix") if isinstance(surface.get("p5a_device_matrix"), dict) else {}
    devices = device_matrix.get("devices") if isinstance(device_matrix.get("devices"), list) else []
    source_reports = evidence.get("source_reports") if isinstance(evidence.get("source_reports"), dict) else {}

    target_surfaces = [
        {"key": "dashboard", "label": "Ana panel / dashboard", "must_check": ["kart taşması yok", "grid tek kolona düşer", "yatay kaydırma yalnız tabloda"]},
        {"key": "home", "label": "Ana sayfa", "must_check": ["hero/özet kartları taşmaz", "butonlar 44px dokunma alanını korur"]},
        {"key": "evaluation_form", "label": "Performans değerlendirme formu", "must_check": ["puanlama alanları alt alta kırılır", "tablo/form taşması kontrollü scroll olur"]},
        {"key": "admin_ai", "label": "Admin AI / karar destek ekranları", "must_check": ["dar ekranlarda kartlar kırılır", "aksiyon butonları satır içinde sıkışmaz"]},
        {"key": "wide_tables", "label": "Geniş tablolar", "must_check": ["tablo dış container taşmaz", "scroll sadece tablo içinde kalır"]},
        {"key": "wide_forms", "label": "Geniş formlar", "must_check": ["input/select/textarea tam genişlik olur", "label-input düzeni okunur kalır"]},
        {"key": "android_small", "label": "Küçük Android ekran", "must_check": ["360px genişlikte yatay gövde taşması yok", "modal/sidebar ekranı kaplamaz"]},
        {"key": "landscape", "label": "Android landscape", "must_check": ["yükseklik daralınca içerik scroll edilebilir", "üst menü/butonlar üst üste binmez"]},
    ]
    observed_flags = surface.get("expected_surface_flags") if isinstance(surface.get("expected_surface_flags"), dict) else {}
    for item in target_surfaces:
        item["covered_by_release_suite"] = bool(observed_flags.get(item["key"], item["key"] in EXPECTED_SURFACES))

    return {
        "ok": bool(
            p5d.get("_exists")
            and p5d.get("ok")
            and p5d.get("android_responsive_release_suite_gate_ok")
            and int(p5d.get("android_device_matrix_count", 0) or 0) >= MIN_ANDROID_DEVICE_COUNT
            and int(p5d.get("target_surface_count", 0) or 0) >= MIN_TARGET_SURFACE_COUNT
            and int(p5d.get("responsive_marker_total", 0) or 0) >= MIN_RESPONSIVE_MARKER_TOTAL
            and bool(p5d.get("responsive_css_evidence_ok"))
            and bool(p5d.get("base_template_links_ok"))
        ),
        "source_p5d_report": p5d.get("_path", ""),
        "source_reports": source_reports,
        "device_count": int(p5d.get("android_device_matrix_count", 0) or 0),
        "devices": devices,
        "target_surface_count": int(p5d.get("target_surface_count", 0) or 0),
        "target_surface_exists_count": int(p5d.get("target_surface_exists_count", 0) or 0),
        "responsive_marker_total": int(p5d.get("responsive_marker_total", 0) or 0),
        "target_surfaces": target_surfaces,
        "acceptance_rules": [
            "360px küçük Android genişlikte gövde yatay taşma üretmemeli.",
            "393/412px standart Android genişliklerinde kart ve form düzeni okunur kalmalı.",
            "600/768px fold-tablet aralığında gereksiz tek kolon sıkışması olmamalı.",
            "Landscape görünümde üst menü, modal, tablo ve form alanları çakışmamalı.",
            "Geniş tablolar yalnız kendi container içinde yatay scroll kullanmalı.",
            "Form inputları, selectler ve aksiyon butonları dokunma alanını korumalı.",
            "P5B ve P5C CSS dosyaları base.html üzerinden yüklü kalmalı.",
        ],
    }


def _write_checklist(root: Path, plan: Dict[str, Any], screenshot: Dict[str, Any]) -> Dict[str, Any]:
    checklist = root / CHECKLIST_REL
    devices = plan.get("devices") if isinstance(plan.get("devices"), list) else []
    target_surfaces = plan.get("target_surfaces") if isinstance(plan.get("target_surfaces"), list) else []
    lines: List[str] = []
    lines.append("# BYS360 Android Responsive Visual UAT Checklist - P5E")
    lines.append("")
    lines.append(f"Olusturma zamani: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Kaynak kanit")
    lines.append("")
    lines.append(f"- P5D V2 release suite: `{plan.get('source_p5d_report', '')}`")
    lines.append(f"- Cihaz sayisi: {plan.get('device_count')}")
    lines.append(f"- Hedef yuzey sayisi: {plan.get('target_surface_count')}")
    lines.append(f"- Responsive marker toplam: {plan.get('responsive_marker_total')}")
    lines.append("")
    lines.append("## Android cihaz matrisi")
    lines.append("")
    lines.append("| Durum | Genislik | Yukseklik | Yon | Not |")
    lines.append("|---|---:|---:|---|---|")
    for device in devices:
        if not isinstance(device, dict):
            continue
        lines.append(f"| {device.get('label','')} | {device.get('width','')} | {device.get('height','')} | {device.get('orientation','')} | Kontrol edildi / edilecek |")
    lines.append("")
    lines.append("## Hedef ekran/yuzey kontrolleri")
    lines.append("")
    for surface in target_surfaces:
        if not isinstance(surface, dict):
            continue
        lines.append(f"### {surface.get('label', surface.get('key', 'Yuzey'))}")
        lines.append("")
        lines.append(f"- Release suite kapsami: {'EVET' if surface.get('covered_by_release_suite') else 'HAYIR'}")
        for rule in surface.get("must_check", []):
            lines.append(f"- [ ] {rule}")
        lines.append("")
    lines.append("## Kabul kurallari")
    lines.append("")
    for rule in plan.get("acceptance_rules", []):
        lines.append(f"- [ ] {rule}")
    lines.append("")
    lines.append("## Opsiyonel ekran goruntusu kaniti")
    lines.append("")
    lines.append(f"- Klasor: `{screenshot.get('path')}`")
    lines.append(f"- Bulunan ekran goruntusu sayisi: {screenshot.get('screenshot_count')}")
    lines.append("- Not: P5E icin screenshot zorunlu degildir; gorsel UAT sonrasi bu klasore eklenirse raporda sayilir.")
    lines.append("")
    _write_text(checklist, "\n".join(lines).rstrip() + "\n")
    return {"path": str(checklist), "exists": checklist.exists(), "line_count": _line_count(checklist), "ok": checklist.exists() and _line_count(checklist) >= 30}


def run_gate(args: argparse.Namespace) -> Dict[str, Any]:
    root = Path(args.root).resolve()
    report_path = root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)

    active_scope = _ensure_active_scope_marker(root)
    inventory = _mobile_inventory(root)
    p5d = _read_json(root / P5D_REPORT_REL)
    plan = _build_visual_uat_plan(p5d)
    screenshot = _collect_screenshot_evidence(root)
    checklist = _write_checklist(root, plan, screenshot)

    visual_uat_evidence_ok = bool(plan.get("ok") and checklist.get("ok"))
    handover_evidence_ok = bool(visual_uat_evidence_ok and p5d.get("_exists") and p5d.get("ok"))
    screenshot_evidence_optional_ok = True

    compile_results: List[Dict[str, Any]] = []
    if args.compile_all:
        compile_results = _compile_files([
            root / "scripts" / "quality" / "bys360_android_responsive_visual_uat_evidence_gate_p5e.py",
            root / "tests" / "architecture" / "test_android_responsive_visual_uat_evidence_p5e.py",
            root / "tests" / "architecture" / "conftest.py",
            root / "scripts" / "quality" / "bys360_android_responsive_release_suite_gate_p5d_v2.py",
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

    ok = bool(
        visual_uat_evidence_ok
        and handover_evidence_ok
        and direct_contract_ok
        and compile_ok
        and app_factory.get("ok")
        and secret.get("ok")
        and secret_count == 0
        and pytest.get("ok")
    )
    output: Dict[str, Any] = {
        "ok": ok,
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "android_responsive_visual_uat_evidence_gate_ok": visual_uat_evidence_ok,
        "visual_uat_evidence_ok": visual_uat_evidence_ok,
        "handover_evidence_ok": handover_evidence_ok,
        "p5d_release_suite_report_ok": bool(p5d.get("_exists") and p5d.get("ok") and p5d.get("android_responsive_release_suite_gate_ok")),
        "visual_uat_checklist_ok": bool(checklist.get("ok")),
        "visual_uat_checklist_path": checklist.get("path"),
        "visual_uat_device_count": plan.get("device_count"),
        "visual_uat_surface_count": plan.get("target_surface_count"),
        "screenshot_evidence_optional_ok": screenshot_evidence_optional_ok,
        "screenshot_count": screenshot.get("screenshot_count"),
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
        "pytest_mode": pytest.get("mode", "pytest_targeted_android_responsive_visual_uat_evidence_p5e"),
        "active_scope": active_scope,
        "inventory": inventory,
        "visual_uat_evidence": {
            "ok": visual_uat_evidence_ok,
            "plan": plan,
            "checklist": checklist,
            "screenshot_evidence": screenshot,
            "source_reports": {"p5d_v2": str(root / P5D_REPORT_REL)},
        },
        "compile_results": compile_results,
        "app_factory_smoke": app_factory,
        "secret_gate": secret,
        "pytest": pytest,
        "ci_commands": [
            "python -m pip install -r requirements-dev.txt",
            "python -m pytest tests/architecture -q",
            "python scripts/quality/bys360_android_responsive_visual_uat_evidence_gate_p5e.py --root . --compile-all --app-factory --secret-gate --pytest-gate",
        ],
        "report": str(report_path),
        "next_actions": [
            "P5E temizse Android responsive görsel UAT checklist ve teslim kanıtı standart kabul edilebilir.",
            "P5F'de gerçek görsel UAT bulgularına göre tekil ekran patchleri veya screenshot regression kanıtları eklenebilir.",
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
        "android_responsive_visual_uat_evidence_gate_ok",
        "visual_uat_evidence_ok",
        "handover_evidence_ok",
        "p5d_release_suite_report_ok",
        "visual_uat_checklist_ok",
        "visual_uat_device_count",
        "visual_uat_surface_count",
        "screenshot_evidence_optional_ok",
        "screenshot_count",
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
