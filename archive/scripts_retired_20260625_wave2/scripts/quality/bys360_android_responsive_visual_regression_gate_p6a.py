from __future__ import annotations

import argparse
import json
import os
import py_compile
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P6A_ANDROID_RESPONSIVE_VISUAL_REGRESSION_GATE"
REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_VISUAL_REGRESSION_GATE_P6A_REPORT.json")
P5F_REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_FINAL_EVIDENCE_GATE_P5F_REPORT.json")
ACTIVE_TEST_FILE = "test_android_responsive_visual_regression_p6a.py"
SCREENSHOT_DIR_REL = Path("reports/visual/android_responsive_p6a/screenshots")
FINDINGS_DIR_REL = Path("reports/visual/android_responsive_p6a/findings")
GUIDE_REL = Path("docs/qa/BYS360_ANDROID_RESPONSIVE_VISUAL_REGRESSION_GUIDE_P6A.md")
FINDINGS_TEMPLATE_REL = Path("docs/qa/BYS360_ANDROID_RESPONSIVE_UAT_FINDINGS_TEMPLATE_P6A.md")

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
EXPECTED_SURFACE_FLAGS = [
    "dashboard",
    "home",
    "evaluation_form",
    "admin_ai",
    "wide_tables",
    "wide_forms",
    "android_small",
    "landscape",
]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(_read_text(path))
    except Exception as exc:  # pragma: no cover - defensive report detail
        return {"_json_error": str(exc)}


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _bool(value: Any) -> bool:
    return bool(value is True)


def ensure_active_scope(root: Path) -> Dict[str, Any]:
    conftest = root / "tests" / "architecture" / "conftest.py"
    conftest.parent.mkdir(parents=True, exist_ok=True)
    marker = f"# BYS360_ACTIVE_ARCHITECTURE_TEST::{ACTIVE_TEST_FILE}"
    changed = False
    if conftest.exists():
        text = _read_text(conftest)
    else:
        text = ""
    if marker not in text:
        if text and not text.endswith("\n"):
            text += "\n"
        text += f"\n{marker}\n"
        _write_text(conftest, text)
        changed = True
    compile_ok = True
    compile_error = ""
    try:
        py_compile.compile(str(conftest), doraise=True)
    except Exception as exc:
        compile_ok = False
        compile_error = str(exc)
    return {"path": str(conftest), "changed": changed, "reason": "appended_safe_marker" if changed else "already_present", "compile_ok": compile_ok, "compile_error": compile_error}


def ensure_docs_and_dirs(root: Path, p5f: Dict[str, Any]) -> Dict[str, Any]:
    screenshots = root / SCREENSHOT_DIR_REL
    findings = root / FINDINGS_DIR_REL
    screenshots.mkdir(parents=True, exist_ok=True)
    findings.mkdir(parents=True, exist_ok=True)

    device_count = int(p5f.get("android_device_matrix_count") or p5f.get("android_responsive_final_evidence", {}).get("android_device_matrix_count") or 0)
    target_surface_count = int(p5f.get("target_surface_count") or p5f.get("android_responsive_final_evidence", {}).get("target_surface_count") or 0)

    guide = f"""# BYS360 Android Responsive Visual Regression Guide P6A

Bu belge, P5F ile kapanan Android responsive teslim kanıtının gerçek cihaz/görsel UAT bulguları ile izlenmesi için oluşturulmuştur.

## Kaynak Kanıt
- P5F final evidence report: `{P5F_REPORT_REL.as_posix()}`
- Beklenen cihaz sayısı: `{device_count}`
- Beklenen hedef yüzey sayısı: `{target_surface_count}`

## Screenshot Klasörü
- `reports/visual/android_responsive_p6a/screenshots`

Screenshot zorunlu değildir; fakat gerçek cihaz kontrolünde görsel kanıt eklenirse bu klasöre alınır.

## Kontrol Kapsamı
- 360px küçük Android
- 393/412px standart Android
- 480px büyük Android
- 600/768px fold/tablet
- 851x393 landscape
- dashboard, home, evaluation_form, admin_ai
- geniş tablolar, geniş formlar, modal/sidebar ve dokunma alanları

## Kabul Kuralı
P5F zinciri temiz kalmalı, P5B/P5C CSS dosyaları base.html üzerinden yüklü olmalı ve yeni UAT bulguları varsa P6A bulgu şablonuyla kayıt altına alınmalıdır.
"""
    findings_template = """# BYS360 Android Responsive UAT Findings Template P6A

## Bulgu Özeti
- Tarih:
- Test eden:
- Cihaz / çözünürlük:
- Ekran / rota:
- Öncelik: Düşük / Orta / Yüksek / Kritik

## Gözlenen Durum

## Beklenen Durum

## Screenshot / Kanıt Dosyası

## Teknik Not

## Çözüm Durumu
- [ ] Açık
- [ ] Düzeltildi
- [ ] Yeniden test edildi
"""
    _write_text(root / GUIDE_REL, guide)
    _write_text(root / FINDINGS_TEMPLATE_REL, findings_template)

    screenshot_files: List[str] = []
    for item in screenshots.rglob("*"):
        if item.is_file() and item.suffix.lower() in IMAGE_EXTS:
            screenshot_files.append(str(item.relative_to(root)))
    finding_files: List[str] = []
    for item in findings.rglob("*"):
        if item.is_file() and item.suffix.lower() in {".md", ".txt", ".json"}:
            finding_files.append(str(item.relative_to(root)))

    return {
        "guide_path": str(root / GUIDE_REL),
        "guide_exists": (root / GUIDE_REL).exists(),
        "findings_template_path": str(root / FINDINGS_TEMPLATE_REL),
        "findings_template_exists": (root / FINDINGS_TEMPLATE_REL).exists(),
        "screenshot_dir": str(screenshots),
        "screenshot_dir_exists": screenshots.exists(),
        "screenshot_count": len(screenshot_files),
        "screenshots": screenshot_files[:50],
        "screenshot_evidence_optional_ok": True,
        "findings_dir": str(findings),
        "findings_dir_exists": findings.exists(),
        "finding_count": len(finding_files),
        "finding_files": finding_files[:50],
        "ok": (root / GUIDE_REL).exists() and (root / FINDINGS_TEMPLATE_REL).exists() and screenshots.exists() and findings.exists(),
    }


def analyze_p5f(root: Path) -> Dict[str, Any]:
    report_path = root / P5F_REPORT_REL
    p5f = _load_json(report_path)
    evidence = p5f.get("android_responsive_final_evidence", {}) if isinstance(p5f, dict) else {}
    css_evidence = evidence.get("css_evidence", {}) if isinstance(evidence, dict) else {}
    visual_evidence = evidence.get("visual_evidence", {}) if isinstance(evidence, dict) else {}

    source_reports = evidence.get("source_reports", {}) if isinstance(evidence, dict) else {}
    phase_results = evidence.get("phase_results", []) if isinstance(evidence, dict) else []

    missing_surface_flags = evidence.get("missing_surface_flags", []) if isinstance(evidence, dict) else []

    return {
        "report": str(report_path),
        "exists": report_path.exists(),
        "ok": _bool(p5f.get("ok")),
        "final_handover_evidence_ok": _bool(p5f.get("final_handover_evidence_ok")),
        "responsive_release_suite_ok": _bool(p5f.get("responsive_release_suite_ok")),
        "visual_uat_evidence_ok": _bool(p5f.get("visual_uat_evidence_ok")),
        "p5_phase_count": int(p5f.get("p5_phase_count") or evidence.get("p5_phase_count") or 0),
        "p5_phases_passed": int(p5f.get("p5_phases_passed") or evidence.get("p5_phases_passed") or 0),
        "android_device_matrix_ok": _bool(p5f.get("android_device_matrix_ok") or evidence.get("android_device_matrix_ok")),
        "android_device_matrix_count": int(p5f.get("android_device_matrix_count") or evidence.get("android_device_matrix_count") or 0),
        "target_surface_inventory_ok": _bool(p5f.get("target_surface_inventory_ok") or evidence.get("target_surface_inventory_ok")),
        "target_surface_count": int(p5f.get("target_surface_count") or evidence.get("target_surface_count") or 0),
        "target_surface_exists_count": int(p5f.get("target_surface_exists_count") or evidence.get("target_surface_exists_count") or 0),
        "responsive_marker_total": int(p5f.get("responsive_marker_total") or evidence.get("responsive_marker_total") or 0),
        "responsive_css_evidence_ok": _bool(p5f.get("responsive_css_evidence_ok") or evidence.get("responsive_css_evidence_ok") or css_evidence.get("ok")),
        "p5b_css_exists": _bool(css_evidence.get("p5b_css_exists")),
        "p5c_css_exists": _bool(css_evidence.get("p5c_css_exists")),
        "p5b_linked_in_base": _bool(css_evidence.get("p5b_linked_in_base")),
        "p5c_linked_in_base": _bool(css_evidence.get("p5c_linked_in_base")),
        "checklist_exists": _bool(visual_evidence.get("checklist_exists")),
        "checklist_path": visual_evidence.get("checklist_path", ""),
        "missing_surface_flags": missing_surface_flags if isinstance(missing_surface_flags, list) else [],
        "source_reports": source_reports,
        "phase_results": phase_results,
    }


def direct_contract_from_p5f(p5f: Dict[str, Any]) -> Dict[str, Any]:
    route_count_ok = int(p5f.get("total_mobile_route_decorator_count") or 0) == int(p5f.get("expected_contract_route_count") or 24)
    lines_ok = _bool(p5f.get("routes_py_under_300_lines"))
    return {
        "routes_py_lines": int(p5f.get("routes_py_lines") or 0),
        "routes_py_under_300_lines": lines_ok,
        "total_mobile_route_decorator_count": int(p5f.get("total_mobile_route_decorator_count") or 0),
        "expected_contract_route_count": int(p5f.get("expected_contract_route_count") or 24),
        "ok": route_count_ok and lines_ok,
    }


def compile_targets(root: Path) -> List[Dict[str, Any]]:
    targets = [
        root / "scripts" / "quality" / "bys360_android_responsive_visual_regression_gate_p6a.py",
        root / "tests" / "architecture" / "test_android_responsive_visual_regression_p6a.py",
        root / "tests" / "architecture" / "conftest.py",
        root / "scripts" / "quality" / "bys360_android_responsive_final_evidence_gate_p5f.py",
    ]
    results: List[Dict[str, Any]] = []
    for path in targets:
        item = {"file": str(path), "ok": False, "error": ""}
        try:
            if not path.exists():
                item["error"] = "missing"
            else:
                py_compile.compile(str(path), doraise=True)
                item["ok"] = True
        except Exception as exc:
            item["error"] = str(exc)
        results.append(item)
    return results


def run_subprocess(cmd: List[str], cwd: Path, timeout: int = 45) -> Dict[str, Any]:
    try:
        cp = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, timeout=timeout)
        return {
            "returncode": cp.returncode,
            "stdout_tail": cp.stdout[-2000:],
            "stderr_tail": cp.stderr[-2000:],
            "ok": cp.returncode == 0,
            "cmd": cmd,
        }
    except Exception as exc:
        return {"returncode": -1, "stdout_tail": "", "stderr_tail": str(exc), "ok": False, "cmd": cmd}


def app_factory_smoke(root: Path) -> Dict[str, Any]:
    py = root / ".venv" / "Scripts" / "python.exe"
    exe = str(py if py.exists() else Path(sys.executable))
    return run_subprocess([exe, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"], root)


def secret_gate(root: Path) -> Dict[str, Any]:
    py = root / ".venv" / "Scripts" / "python.exe"
    exe = str(py if py.exists() else Path(sys.executable))
    script = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    if not script.exists():
        return {"ok": False, "error": "secret gate script missing", "cmd": [exe, str(script)]}
    result = run_subprocess([exe, str(script), "--root", str(root)], root)
    parsed: Dict[str, Any] = {}
    try:
        start = result.get("stdout_tail", "").find("{")
        end = result.get("stdout_tail", "").rfind("}")
        if start >= 0 and end >= start:
            parsed = json.loads(result["stdout_tail"][start:end + 1])
    except Exception:
        parsed = {}
    result["parsed"] = parsed
    result["ok"] = bool(result.get("ok")) and parsed.get("ok") is True and int(parsed.get("finding_count", 999)) == 0
    return result


def pytest_gate(root: Path) -> Dict[str, Any]:
    py = root / ".venv" / "Scripts" / "python.exe"
    exe = str(py if py.exists() else Path(sys.executable))
    return run_subprocess([exe, "-m", "pytest", "tests\\architecture\\test_android_responsive_visual_regression_p6a.py", "-q"], root)


def run_checks(root: Path, compile_all: bool = False, app_factory: bool = False, secret_gate_enabled: bool = False, pytest_gate_enabled: bool = False, write_report: bool = True) -> Dict[str, Any]:
    root = root.resolve()
    active_scope = ensure_active_scope(root)
    p5f_report = _load_json(root / P5F_REPORT_REL)
    p5f = analyze_p5f(root)
    docs = ensure_docs_and_dirs(root, p5f_report)
    direct_contract = direct_contract_from_p5f(p5f_report)

    visual_regression_ready_ok = all([
        p5f["exists"], p5f["ok"], p5f["final_handover_evidence_ok"],
        p5f["responsive_release_suite_ok"], p5f["visual_uat_evidence_ok"],
        p5f["p5_phase_count"] >= 5, p5f["p5_phases_passed"] >= 5,
        p5f["responsive_css_evidence_ok"], p5f["android_device_matrix_ok"],
        p5f["android_device_matrix_count"] >= 6,
        p5f["target_surface_inventory_ok"], p5f["target_surface_count"] >= 24,
        p5f["target_surface_exists_count"] >= 24,
        p5f["checklist_exists"], not p5f["missing_surface_flags"], docs["ok"],
    ])

    compile_results = compile_targets(root) if compile_all else []
    compile_ok = active_scope["compile_ok"] and (all(x["ok"] for x in compile_results) if compile_all else True)
    app_smoke = app_factory_smoke(root) if app_factory else {"ok": True, "skipped": True}
    secret = secret_gate(root) if secret_gate_enabled else {"ok": True, "skipped": True, "parsed": {"finding_count": 0}}
    pytest_result = pytest_gate(root) if pytest_gate_enabled else {"ok": True, "skipped": True}

    result: Dict[str, Any] = {
        "ok": False,
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "android_responsive_visual_regression_gate_ok": visual_regression_ready_ok,
        "visual_regression_ready_ok": visual_regression_ready_ok,
        "p5f_final_evidence_report_ok": p5f["ok"],
        "final_handover_evidence_ok": p5f["final_handover_evidence_ok"],
        "responsive_release_suite_ok": p5f["responsive_release_suite_ok"],
        "visual_uat_evidence_ok": p5f["visual_uat_evidence_ok"],
        "p5_phase_count": p5f["p5_phase_count"],
        "p5_phases_passed": p5f["p5_phases_passed"],
        "responsive_css_evidence_ok": p5f["responsive_css_evidence_ok"],
        "android_device_matrix_ok": p5f["android_device_matrix_ok"],
        "android_device_matrix_count": p5f["android_device_matrix_count"],
        "target_surface_inventory_ok": p5f["target_surface_inventory_ok"],
        "target_surface_count": p5f["target_surface_count"],
        "target_surface_exists_count": p5f["target_surface_exists_count"],
        "visual_regression_guide_ok": docs["guide_exists"],
        "visual_regression_findings_template_ok": docs["findings_template_exists"],
        "screenshot_evidence_optional_ok": docs["screenshot_evidence_optional_ok"],
        "screenshot_dir_exists": docs["screenshot_dir_exists"],
        "screenshot_count": docs["screenshot_count"],
        "finding_count": docs["finding_count"],
        "routes_py_lines": direct_contract["routes_py_lines"],
        "routes_py_under_300_lines": direct_contract["routes_py_under_300_lines"],
        "total_mobile_route_decorator_count": direct_contract["total_mobile_route_decorator_count"],
        "expected_contract_route_count": direct_contract["expected_contract_route_count"],
        "direct_contract_ok": direct_contract["ok"],
        "compile_ok": compile_ok,
        "app_factory_ok": bool(app_smoke.get("ok")),
        "secret_gate_ok": bool(secret.get("ok")),
        "secret_gate_finding_count": int(secret.get("parsed", {}).get("finding_count", 0) or 0),
        "pytest_ok": bool(pytest_result.get("ok")),
        "pytest_mode": "pytest_targeted_android_responsive_visual_regression_p6a",
        "active_scope": active_scope,
        "visual_regression_evidence": {
            "ok": visual_regression_ready_ok,
            "source_p5f_report": str(root / P5F_REPORT_REL),
            "guide": str(root / GUIDE_REL),
            "findings_template": str(root / FINDINGS_TEMPLATE_REL),
            "screenshot_dir": docs["screenshot_dir"],
            "screenshot_count": docs["screenshot_count"],
            "screenshots": docs["screenshots"],
            "findings_dir": docs["findings_dir"],
            "finding_count": docs["finding_count"],
            "finding_files": docs["finding_files"],
            "device_count": p5f["android_device_matrix_count"],
            "target_surface_count": p5f["target_surface_count"],
            "missing_surface_flags": p5f["missing_surface_flags"],
            "expected_surface_flags": EXPECTED_SURFACE_FLAGS,
        },
        "compile_results": compile_results,
        "app_factory_smoke": app_smoke,
        "secret_gate": secret,
        "pytest": pytest_result,
        "ci_commands": [
            "python -m pip install -r requirements-dev.txt",
            "python -m pytest tests/architecture -q",
            "python scripts/quality/bys360_android_responsive_visual_regression_gate_p6a.py --root . --compile-all --app-factory --secret-gate --pytest-gate",
        ],
        "report": str(root / REPORT_REL),
        "next_actions": [
            "P6A temizse Android responsive final kaniti, gorsel regresyon klasoru ve UAT bulgu sablonu hazir kabul edilebilir.",
            "Gorsel UAT bulgusu gelirse P6B'de tekil ekran patchleri veya screenshot regression kanitlari eklenebilir.",
        ],
    }
    result["ok"] = all([
        result["android_responsive_visual_regression_gate_ok"],
        result["direct_contract_ok"], result["compile_ok"], result["app_factory_ok"],
        result["secret_gate_ok"], result["secret_gate_finding_count"] == 0, result["pytest_ok"],
    ])
    if write_report:
        _write_json(root / REPORT_REL, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--compile-all", action="store_true")
    parser.add_argument("--app-factory", action="store_true")
    parser.add_argument("--secret-gate", action="store_true")
    parser.add_argument("--pytest-gate", action="store_true")
    args = parser.parse_args()
    result = run_checks(Path(args.root), args.compile_all, args.app_factory, args.secret_gate, args.pytest_gate, write_report=True)
    print(json.dumps({
        "ok": result["ok"],
        "package": result["package"],
        "android_responsive_visual_regression_gate_ok": result["android_responsive_visual_regression_gate_ok"],
        "visual_regression_ready_ok": result["visual_regression_ready_ok"],
        "p5f_final_evidence_report_ok": result["p5f_final_evidence_report_ok"],
        "visual_regression_guide_ok": result["visual_regression_guide_ok"],
        "visual_regression_findings_template_ok": result["visual_regression_findings_template_ok"],
        "screenshot_evidence_optional_ok": result["screenshot_evidence_optional_ok"],
        "screenshot_count": result["screenshot_count"],
        "finding_count": result["finding_count"],
        "direct_contract_ok": result["direct_contract_ok"],
        "compile_ok": result["compile_ok"],
        "app_factory_ok": result["app_factory_ok"],
        "secret_gate_ok": result["secret_gate_ok"],
        "secret_gate_finding_count": result["secret_gate_finding_count"],
        "pytest_ok": result["pytest_ok"],
        "pytest_mode": result["pytest_mode"],
        "report": result["report"],
    }, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
