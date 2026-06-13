from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


TARGET_REL = "app/static/js/bys360_assistant_module.js"
HELPER_REL = "app/static/js/bys360_assistant_helpers_v1.js"
P14_E2_APPLIED_REL = "reports/quality/bys360_quality_10_10_p14_e2_assistant_js_helper_split_safe_apply_applied_v1.json"
P12_B_REL = "reports/quality/bys360_quality_10_10_p12_b_technical_ui_term_decision_v1.json"


EXPECTED_HELPERS = [
    "iconSpark",
    "listToSentence",
    "uniqueWeatherPaths",
    "weatherCodeText",
    "isSnowLikeText",
    "isSnowCode",
    "isWeatherConditionTemperatureMismatch",
    "safeWeatherCondition",
    "weatherTone",
    "cleanSmallText",
    "cleanText",
    "weatherConsistency",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def load_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(read_text(path))
    except Exception as exc:
        print(f"BYS360_P14_F_JSON_READ_WARN path={path} error={exc}")
        return None


def run_cmd(project_root: Path, cmd: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        cmd,
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "cmd": cmd,
        "returncode": completed.returncode,
        "stdout": completed.stdout or "",
        "stderr": completed.stderr or "",
    }


def run_p7(project_root: Path) -> dict[str, Any]:
    script = project_root / "scripts/windows/analyze_bys360_quality_10_10_p7_findings.ps1"
    if not script.exists():
        return {"error": f"P7_SCRIPT_NOT_FOUND: {script}"}
    result = run_cmd(project_root, [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-ProjectRoot",
        str(project_root),
        "-Level",
        "P1",
        "-Limit",
        "240",
    ])
    parsed = parse_p7_stdout(result["stdout"])
    result["parsed"] = parsed
    return result


def run_clean_audit(project_root: Path) -> dict[str, Any]:
    script = project_root / "scripts/windows/check_bys360_quality_10_10_p3_clean_audit.ps1"
    if not script.exists():
        return {"error": f"CLEAN_AUDIT_SCRIPT_NOT_FOUND: {script}"}
    result = run_cmd(project_root, [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-ProjectRoot",
        str(project_root),
        "-FailOn",
        "never",
    ])
    result["parsed"] = parse_clean_audit_stdout(result["stdout"])
    return result


def parse_clean_audit_stdout(stdout: str) -> dict[str, Any]:
    m = re.search(r"BYS360_QUALITY_10_10_CLEAN_AUDIT_SUMMARY\s*\n(\{[^\n]+\})", stdout)
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except Exception:
        return {}


def parse_p7_stdout(stdout: str) -> dict[str, Any]:
    raw_match = re.search(r"P1_findings_found=(\d+)", stdout)
    raw_p1 = int(raw_match.group(1)) if raw_match else None

    rule_summary: dict[str, int] = {}
    path_summary: dict[str, int] = {}
    first_findings: list[dict[str, Any]] = []

    mode = None
    current: dict[str, Any] | None = None
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped == "BYS360_QUALITY_10_10_P7_RULE_SUMMARY":
            mode = "rule"
            continue
        if stripped == "BYS360_QUALITY_10_10_P7_PATH_SUMMARY":
            mode = "path"
            continue
        if stripped == "BYS360_QUALITY_10_10_P7_FIRST_FINDINGS":
            mode = "first"
            continue
        if stripped.startswith("BYS360_QUALITY_10_10_P7_") and stripped not in {
            "BYS360_QUALITY_10_10_P7_RULE_SUMMARY",
            "BYS360_QUALITY_10_10_P7_PATH_SUMMARY",
            "BYS360_QUALITY_10_10_P7_FIRST_FINDINGS",
        }:
            mode = None

        if mode in {"rule", "path"}:
            m = re.match(r"^\s*(\d+)\s*\|\s*(.+?)\s*$", line)
            if m:
                if mode == "rule":
                    rule_summary[m.group(2).strip()] = int(m.group(1))
                else:
                    path_summary[m.group(2).strip()] = int(m.group(1))

        if mode == "first":
            m = re.match(r"^\[(\d+)\]\s+path=(.*?)\s+line=(.*?)\s+rule=([A-Z0-9_]+)\s*$", stripped)
            if m:
                current = {
                    "index": int(m.group(1)),
                    "path": m.group(2).strip(),
                    "line": m.group(3).strip(),
                    "rule": m.group(4).strip(),
                    "message": "",
                }
                first_findings.append(current)
                continue
            if current is not None and stripped.startswith("message="):
                current["message"] = stripped.split("=", 1)[1]

    return {
        "raw_p1": raw_p1,
        "rule_summary": rule_summary,
        "path_summary": path_summary,
        "first_findings": first_findings,
    }


def helper_checks(project_root: Path) -> dict[str, Any]:
    target = project_root / TARGET_REL
    helper = project_root / HELPER_REL
    base = project_root / "app/templates/base.html"

    target_exists = target.exists()
    helper_exists = helper.exists()
    base_exists = base.exists()

    target_text = read_text(target) if target_exists else ""
    helper_text = read_text(helper) if helper_exists else ""
    base_text = read_text(base) if base_exists else ""

    wrapper_hits = {}
    helper_exports = {}
    missing_wrappers = []
    missing_exports = []

    for name in EXPECTED_HELPERS:
        wrapper_pattern = f"window.BYS360AssistantHelpersV1.{name}.apply"
        export_pattern = f"helpers.{name} = {name};"
        wrapper_hits[name] = wrapper_pattern in target_text
        helper_exports[name] = export_pattern in helper_text
        if not wrapper_hits[name]:
            missing_wrappers.append(name)
        if not helper_exports[name]:
            missing_exports.append(name)

    helper_tag_index = base_text.find("bys360_assistant_helpers_v1.js")
    module_tag_index = base_text.find("bys360_assistant_module.js")
    helper_loaded_before_module = (
        helper_tag_index >= 0 and module_tag_index >= 0 and helper_tag_index < module_tag_index
    )

    return {
        "target_exists": target_exists,
        "helper_exists": helper_exists,
        "base_exists": base_exists,
        "target_line_count": len(target_text.splitlines()) if target_exists else 0,
        "helper_line_count": len(helper_text.splitlines()) if helper_exists else 0,
        "wrapper_hits": wrapper_hits,
        "helper_exports": helper_exports,
        "missing_wrappers": missing_wrappers,
        "missing_exports": missing_exports,
        "base_has_helper_tag": helper_tag_index >= 0,
        "base_has_module_tag": module_tag_index >= 0,
        "helper_loaded_before_module": helper_loaded_before_module,
        "helper_tag_index": helper_tag_index,
        "module_tag_index": module_tag_index,
    }


def classify_new_p1(rule_summary: dict[str, int]) -> dict[str, Any]:
    # Expected before P14-E2 was P1=50, rules 45/4/1.
    baseline = {
        "TECHNICAL_UI_TERM": 45,
        "LARGE_FILE_HARD": 4,
        "MANY_REPAIR_SCRIPTS": 1,
    }
    deltas = {}
    for key, count in rule_summary.items():
        deltas[key] = count - baseline.get(key, 0)
    for key, count in baseline.items():
        if key not in deltas:
            deltas[key] = -count

    likely_reason = []
    if deltas.get("MANY_REPAIR_SCRIPTS", 0) > 0:
        likely_reason.append("P14-E/P14-E2 yeni helper/apply scriptleri script sayısı eşiğini artırmış olabilir.")
    if deltas.get("TECHNICAL_UI_TERM", 0) > 0:
        likely_reason.append("Yeni helper JS veya P14-E scriptleri teknik terim kuralına takılmış olabilir.")
    if deltas.get("LARGE_FILE_HARD", 0) > 0:
        likely_reason.append("Raporlayıcı aynı büyük dosyaları çift sayıyor olabilir veya yeni büyük dosya oluşmuş olabilir.")
    if not likely_reason:
        likely_reason.append("P1 artışı yok veya bilinen baseline ile uyumlu.")

    return {
        "baseline": baseline,
        "deltas": deltas,
        "likely_reason": likely_reason,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    print("BYS360_QUALITY_10_10_P14_F_ASSISTANT_JS_SPLIT_VERIFICATION_START")
    print(f"project_root={project_root}")

    helper_result = helper_checks(project_root)
    clean_result = run_clean_audit(project_root)
    p7_result = run_p7(project_root)

    p7_parsed = p7_result.get("parsed") or {}
    rule_summary = p7_parsed.get("rule_summary") or {}
    p1_deltas = classify_new_p1(rule_summary)

    p14_e2_report = load_json(project_root / P14_E2_APPLIED_REL)
    p12_b_report = load_json(project_root / P12_B_REL)

    verification_ok = (
        helper_result["target_exists"]
        and helper_result["helper_exists"]
        and not helper_result["missing_wrappers"]
        and not helper_result["missing_exports"]
        and helper_result["helper_loaded_before_module"]
        and (clean_result.get("parsed") or {}).get("P0", 999) == 0
    )

    result = {
        "verification_ok": verification_ok,
        "helper_checks": helper_result,
        "clean_audit": {
            "returncode": clean_result.get("returncode"),
            "summary": clean_result.get("parsed"),
            "stdout_tail": (clean_result.get("stdout") or "")[-5000:],
            "stderr_tail": (clean_result.get("stderr") or "")[-3000:],
        },
        "p7_analysis": {
            "returncode": p7_result.get("returncode"),
            "parsed": p7_parsed,
            "stdout_tail": (p7_result.get("stdout") or "")[-8000:],
            "stderr_tail": (p7_result.get("stderr") or "")[-3000:],
        },
        "p1_delta_analysis": p1_deltas,
        "p14_e2_applied_report_loaded": p14_e2_report is not None,
        "p12_b_decision_report_loaded": p12_b_report is not None,
        "recommended_next": {
            "decision": "RUN_BROWSER_SMOKE_TEST_BEFORE_MORE_SPLITS" if verification_ok else "FIX_VERIFICATION_FAILURES",
            "reason": "P14-E2 dosya seviyesinde doğrulandı; artık tarayıcı smoke test gerekir." if verification_ok else "Helper/wrapper/script sırası veya P0 doğrulamasında sorun var.",
        },
        "browser_smoke_test_plan": [
            "Ana sayfayı aç; F12 Console’da hata olmadığını kontrol et.",
            "BYS360 Asistan panelini aç/kapat; panel görünürlüğü ve sürükleme davranışı bozulmamalı.",
            "Asistana “merhaba” yaz; yerel cevap akışı çalışmalı.",
            "Asistana “bu ekranda ne yapabilirim” yaz; ekran bağlamı cevabı gelmeli.",
            "Hava durumu/yerel cevap akışını tetikle; cevap formatı bozulmamalı.",
            "Performans, personel ve destek/talep ekranlarında asistan yönlendirmelerini kontrol et.",
            "Console’da undefined, missing function, CSP veya fetch hatası olmamalı.",
        ],
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p14_f_assistant_js_split_verification_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p14_f_assistant_js_split_verification_v1.md"

    write_text(json_out, json.dumps(result, ensure_ascii=False, indent=2))

    md = []
    md.append("# BYS360 P14-F Assistant JS Split Verification")
    md.append("")
    md.append(f"- Verification OK: {verification_ok}")
    md.append(f"- Helper file exists: {helper_result['helper_exists']}")
    md.append(f"- Target wrappers missing: {helper_result['missing_wrappers']}")
    md.append(f"- Helper exports missing: {helper_result['missing_exports']}")
    md.append(f"- Helper loaded before module: {helper_result['helper_loaded_before_module']}")
    md.append(f"- Clean audit summary: {clean_result.get('parsed')}")
    md.append(f"- P7 rule summary: {rule_summary}")
    md.append("")
    md.append("## P1 Delta Analizi")
    md.append("")
    md.append(f"- Baseline: {p1_deltas['baseline']}")
    md.append(f"- Deltas: {p1_deltas['deltas']}")
    for reason in p1_deltas["likely_reason"]:
        md.append(f"- {reason}")
    md.append("")
    md.append("## Tarayıcı Smoke Test Planı")
    md.append("")
    for idx, item in enumerate(result["browser_smoke_test_plan"], start=1):
        md.append(f"{idx}. {item}")
    md.append("")
    md.append("## Sonraki Karar")
    md.append("")
    md.append(f"- {result['recommended_next']['decision']}: {result['recommended_next']['reason']}")
    write_text(md_out, "\n".join(md) + "\n")

    print(f"verification_ok={verification_ok}")
    print(f"helper_exists={helper_result['helper_exists']}")
    print(f"target_line_count={helper_result['target_line_count']}")
    print(f"helper_line_count={helper_result['helper_line_count']}")
    print(f"missing_wrapper_count={len(helper_result['missing_wrappers'])}")
    print(f"missing_export_count={len(helper_result['missing_exports'])}")
    print(f"base_has_helper_tag={helper_result['base_has_helper_tag']}")
    print(f"base_has_module_tag={helper_result['base_has_module_tag']}")
    print(f"helper_loaded_before_module={helper_result['helper_loaded_before_module']}")
    print("BYS360_QUALITY_10_10_P14_F_CLEAN_AUDIT_SUMMARY")
    print(json.dumps(clean_result.get("parsed") or {}, ensure_ascii=False))
    print("BYS360_QUALITY_10_10_P14_F_P1_RULE_SUMMARY")
    for key, count in (rule_summary or {}).items():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P14_F_P1_DELTA_ANALYSIS")
    print(json.dumps(p1_deltas, ensure_ascii=False))
    print("BYS360_QUALITY_10_10_P14_F_RECOMMENDED_NEXT")
    print(f"decision={result['recommended_next']['decision']}")
    print(f"reason={result['recommended_next']['reason']}")
    print("BYS360_QUALITY_10_10_P14_F_BROWSER_SMOKE_TEST_PLAN")
    for idx, item in enumerate(result["browser_smoke_test_plan"], start=1):
        print(f"{idx}. {item}")
    print(f"assistant_js_split_verification_json={json_out}")
    print(f"assistant_js_split_verification_md={md_out}")
    print("BYS360_QUALITY_10_10_P14_F_ASSISTANT_JS_SPLIT_VERIFICATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
