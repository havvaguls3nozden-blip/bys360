from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


P12_B_REL = "reports/quality/bys360_quality_10_10_p12_b_technical_ui_term_decision_v1.json"

KNOWN_LARGE_FILES = [
    "app/static/js/bys360_assistant_module.js",
    "app/services/settings/effective_menu.py",
    "app/api/mobile/performance_routes.py",
    "app/api/mobile/routes.py",
]


def load_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception as exc:
        print(f"BYS360_P13_A3_JSON_READ_WARN path={path} error={exc}")
        return None


def get_line_count(project_root: Path, rel_path: str) -> int:
    path = project_root / rel_path
    if not path.exists() or not path.is_file():
        return 0
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def run_p7(project_root: Path) -> str:
    script = project_root / "scripts/windows/analyze_bys360_quality_10_10_p7_findings.ps1"
    if not script.exists():
        raise SystemExit(f"P7_SCRIPT_NOT_FOUND: {script}")

    completed = subprocess.run(
        [
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
            "200",
        ],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=False,
    )

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    if completed.returncode != 0:
        raise SystemExit(
            "P7_SCRIPT_FAILED\n"
            + stdout[-4000:]
            + "\n"
            + stderr[-4000:]
        )

    return stdout


def parse_p7_stdout(stdout: str) -> dict[str, Any]:
    raw_match = re.search(r"P1_findings_found=(\d+)", stdout)
    if not raw_match:
        raise SystemExit("P7_RAW_P1_NOT_FOUND_IN_STDOUT")

    raw_p1 = int(raw_match.group(1))

    rule_summary: dict[str, int] = {}
    in_rule_summary = False

    for line in stdout.splitlines():
        if line.strip() == "BYS360_QUALITY_10_10_P7_RULE_SUMMARY":
            in_rule_summary = True
            continue

        if in_rule_summary:
            if line.startswith("BYS360_QUALITY_10_10_P7_") and line.strip() != "BYS360_QUALITY_10_10_P7_RULE_SUMMARY":
                break
            m = re.match(r"^\s*(\d+)\s*\|\s*([A-Z0-9_]+)\s*$", line)
            if m:
                rule_summary[m.group(2)] = int(m.group(1))

    if not rule_summary:
        raise SystemExit("P7_RULE_SUMMARY_NOT_FOUND_IN_STDOUT")

    first_findings: list[dict[str, Any]] = []
    finding_re = re.compile(r"^\[(\d+)\]\s+path=(.*?)\s+line=(.*?)\s+rule=([A-Z0-9_]+)\s*$")
    current: dict[str, Any] | None = None

    for line in stdout.splitlines():
        m = finding_re.match(line.strip())
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
        if current is not None and line.strip().startswith("message="):
            current["message"] = line.strip().split("=", 1)[1]

    return {
        "raw_p1": raw_p1,
        "rule_summary": rule_summary,
        "first_findings": first_findings,
    }


def build_large_file_plan(project_root: Path, rel_path: str) -> dict[str, Any]:
    line_count = get_line_count(project_root, rel_path)

    plan_map = {
        "app/static/js/bys360_assistant_module.js": {
            "phase": "P14-A",
            "decision": "PLAN_DEDICATED_ASSISTANT_JS_INVENTORY_ONLY",
            "risk": "HIGH",
            "reason": "6200+ satırlık asistan JS dosyası ekran zekâsı, yönlendirme ve kullanıcı deneyimi içeriyor; ilk adım sadece envanter olmalı.",
            "next_step": "P14-A assistant JS inventory only.",
        },
        "app/services/settings/effective_menu.py": {
            "phase": "P11-E",
            "decision": "KEEP_WITH_GOVERNANCE_NOTE",
            "risk": "HIGH",
            "reason": "Yetki, kişi bazlı menü görünürlüğü ve DB bağlamı içeriyor; şimdilik bilinçli bırakılmalı.",
            "next_step": "Kod taşıma yok; karar raporunda bilinçli büyük dosya olarak tutulacak.",
        },
        "app/api/mobile/performance_routes.py": {
            "phase": "P11-C",
            "decision": "STOP_AFTER_SAFE_GET_SPLITS",
            "risk": "HIGH",
            "reason": "Güvenli GET endpointler ayrıldı; kalanlar puanlama/onay/yayın/score tarafına kaydı.",
            "next_step": "Şimdilik dur; score_submit yerinde kalmalı.",
        },
        "app/api/mobile/routes.py": {
            "phase": "P11-B",
            "decision": "STOP_AFTER_SAFE_GET_SPLITS",
            "risk": "MEDIUM_HIGH",
            "reason": "Güvenli GET endpointler ayrıldı; kalanlar auth/POST/personel/hassas işlem ağırlıklı.",
            "next_step": "Şimdilik dur; smoke test ve dokümantasyon.",
        },
    }

    base = plan_map.get(rel_path, {})
    return {
        "path": rel_path,
        "line_count": line_count,
        "phase": base.get("phase", "UNPLANNED"),
        "decision": base.get("decision", "REVIEW_REQUIRED"),
        "risk": base.get("risk", "UNKNOWN"),
        "reason": base.get("reason", "Bu büyük dosya için özel plan gerekir."),
        "next_step": base.get("next_step", "Ayrı envanter hazırlanmalı."),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    print("BYS360_QUALITY_10_10_P13_A3_EFFECTIVE_P1_CLOSURE_FROM_P7_START")
    print(f"project_root={project_root}")

    p12_b = load_json(project_root / P12_B_REL)
    if p12_b is None:
        raise SystemExit(f"P12_B_REPORT_NOT_FOUND: {project_root / P12_B_REL}")

    stdout = run_p7(project_root)
    parsed = parse_p7_stdout(stdout)

    raw_p1 = int(parsed["raw_p1"])
    rule_summary = dict(parsed["rule_summary"])

    technical_count = int(rule_summary.get("TECHNICAL_UI_TERM", 0))
    accepted_technical_reported = int(p12_b.get("accepted_false_positive_count") or 0)
    accepted_technical_effective = min(accepted_technical_reported, technical_count)
    manual_review = int(p12_b.get("manual_review_count") or 0)

    effective_p1 = max(0, raw_p1 - accepted_technical_effective)

    large_file_count = int(rule_summary.get("LARGE_FILE_HARD", 0))
    many_repair_count = int(rule_summary.get("MANY_REPAIR_SCRIPTS", 0))
    except_without_log_count = int(rule_summary.get("EXCEPT_WITHOUT_LOG", 0))

    large_file_plan = [build_large_file_plan(project_root, path) for path in KNOWN_LARGE_FILES if (project_root / path).exists()]

    remaining_real_actions = []
    for item in large_file_plan:
        remaining_real_actions.append({
            "category": "LARGE_FILE_HARD",
            "path": item["path"],
            "count": 1,
            "decision": item["decision"],
            "next_step": item["next_step"],
        })

    if many_repair_count:
        remaining_real_actions.append({
            "category": "MANY_REPAIR_SCRIPTS",
            "count": many_repair_count,
            "decision": "GOVERNANCE_ARCHIVE_PLAN",
            "next_step": "P13-B/P13-C raporları karar eki olarak tutulacak; silme yapılmayacak.",
        })

    if except_without_log_count:
        remaining_real_actions.append({
            "category": "EXCEPT_WITHOUT_LOG",
            "count": except_without_log_count,
            "decision": "FIX_REQUIRED",
            "next_step": "P13-F3 tekrar kontrol edilmeli.",
        })

    if manual_review:
        remaining_real_actions.append({
            "category": "TECHNICAL_UI_TERM_MANUAL_REVIEW",
            "count": manual_review,
            "decision": "REVIEW_REQUIRED",
            "next_step": "P12-B manuel inceleme satırları kontrol edilmeli.",
        })

    result = {
        "source": "P13-A3 uses P7 stdout as source of truth",
        "raw_p1": raw_p1,
        "p1_rule_summary_from_p7": rule_summary,
        "technical_ui_term_count": technical_count,
        "accepted_technical_ui_false_positive": accepted_technical_effective,
        "accepted_technical_ui_false_positive_reported_by_p12_b": accepted_technical_reported,
        "manual_review_technical_ui": manual_review,
        "effective_p1": effective_p1,
        "large_file_count_from_p7": large_file_count,
        "many_repair_scripts_count_from_p7": many_repair_count,
        "except_without_log_count_from_p7": except_without_log_count,
        "large_file_plan": large_file_plan,
        "remaining_real_actions": remaining_real_actions,
        "p7_first_findings": parsed["first_findings"],
        "recommended_next": {
            "phase": "P14-A",
            "title": "Assistant JS inventory only",
            "reason": "P0 temiz, EXCEPT_WITHOUT_LOG temiz ve P1 etkili olarak 5; en büyük bilinçli dosya app/static/js/bys360_assistant_module.js.",
        },
        "safety_strategy": [
            "P13-A3 P1 sayısını clean JSON içindeki belirsiz alanlardan değil, P7 stdout değerlerinden okur.",
            "TECHNICAL_UI_TERM bulguları P12-B karar raporuna göre false positive olarak kabul edilir.",
            "Büyük dosyalarda bu aşamada kod parçalama yok; sadece faz bazlı karar/enzanter yapılır.",
            "MANY_REPAIR_SCRIPTS için silme yok; arşiv planı/dry-run raporları karar eki olarak tutulur.",
        ],
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p13_a3_effective_p1_closure_from_p7_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p13_a3_effective_p1_closure_from_p7_v1.md"
    stdout_out = out_dir / "bys360_quality_10_10_p13_a3_source_p7_stdout_v1.txt"

    json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    stdout_out.write_text(stdout, encoding="utf-8")

    md = []
    md.append("# BYS360 P13-A3 Effective P1 Closure From P7")
    md.append("")
    md.append(f"- Ham P1: {raw_p1}")
    md.append(f"- P1 kural özeti: {rule_summary}")
    md.append(f"- Kabul edilen teknik UI false positive: {accepted_technical_effective}")
    md.append(f"- Teknik UI manuel inceleme: {manual_review}")
    md.append(f"- Etkili P1: {effective_p1}")
    md.append("")
    md.append("## Kalan Gerçek Aksiyonlar")
    md.append("")
    for item in remaining_real_actions:
        if item.get("path"):
            md.append(f"- {item['category']} — `{item['path']}` — {item['decision']} — {item['next_step']}")
        else:
            md.append(f"- {item['category']} — count={item.get('count')} — {item['decision']} — {item['next_step']}")
    md.append("")
    md.append("## Büyük Dosya Planı")
    md.append("")
    for item in large_file_plan:
        md.append(f"- `{item['path']}` ({item['line_count']} satır): {item['decision']} / {item['next_step']}")
    md.append("")
    md.append("## Önerilen Sıradaki Faz")
    md.append("")
    md.append(f"- {result['recommended_next']['phase']}: {result['recommended_next']['title']}")
    md.append(f"- Gerekçe: {result['recommended_next']['reason']}")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"raw_p1={raw_p1}")
    print(f"accepted_technical_ui_false_positive={accepted_technical_effective}")
    print(f"manual_review_technical_ui={manual_review}")
    print(f"effective_p1={effective_p1}")
    print("BYS360_QUALITY_10_10_P13_A3_P1_RULE_SUMMARY_FROM_P7")
    for key, count in rule_summary.items():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P13_A3_LARGE_FILE_PLAN")
    for item in large_file_plan:
        print(f"{item['path']} | lines={item['line_count']} | decision={item['decision']} | risk={item['risk']}")
        print(f"    next={item['next_step']}")
    print("BYS360_QUALITY_10_10_P13_A3_REMAINING_REAL_ACTIONS")
    for item in remaining_real_actions:
        print(json.dumps(item, ensure_ascii=False))
    print(f"effective_p1_closure_from_p7_json={json_out}")
    print(f"effective_p1_closure_from_p7_md={md_out}")
    print(f"source_p7_stdout={stdout_out}")
    print("BYS360_QUALITY_10_10_P13_A3_EFFECTIVE_P1_CLOSURE_FROM_P7_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
