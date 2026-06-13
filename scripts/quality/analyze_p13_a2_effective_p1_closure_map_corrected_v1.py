from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


P12_B_REL = "reports/quality/bys360_quality_10_10_p12_b_technical_ui_term_decision_v1.json"
P1_ANALYSIS_REL = "reports/quality/bys360_quality_10_10_p1_analysis_v1.json"
CLEAN_REPORT_REL = "reports/quality/bys360_quality_10_10_audit_v1_clean.json"


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
    except Exception:
        return None


def get_any(obj: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in obj:
            return obj.get(key)
    lower = {str(k).lower(): v for k, v in obj.items()}
    for key in keys:
        if key.lower() in lower:
            return lower[key.lower()]
    return None


def normalize_path(value: Any) -> str:
    return str(value or "").replace("\\", "/").strip()


def recursive_findings(obj: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        # Prefer actual finding-shaped dicts, but keep this broad for existing reports.
        if any(k in obj for k in ("rule", "rule_id", "severity", "level", "path", "file", "message")):
            out.append(obj)
        for value in obj.values():
            out.extend(recursive_findings(value))
    elif isinstance(obj, list):
        for item in obj:
            out.extend(recursive_findings(item))
    return out


def normalize_finding(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": normalize_path(get_any(raw, ["path", "file", "filepath", "relative_path", "Path"])),
        "line": str(get_any(raw, ["line", "line_number", "lineno", "Line", "lineNo"]) or ""),
        "rule": str(get_any(raw, ["rule", "rule_id", "Rule", "ruleName", "code", "check", "id", "name"]) or ""),
        "severity": str(get_any(raw, ["severity", "level", "priority"]) or ""),
        "message": str(get_any(raw, ["message", "Message", "description", "text", "detail"]) or ""),
        "raw": raw,
    }


def classify_rule(item: dict[str, Any]) -> str:
    blob = (
        str(item.get("rule", ""))
        + " "
        + str(item.get("message", ""))
        + " "
        + json.dumps(item.get("raw", {}), ensure_ascii=False)
    ).lower()
    if "technical_ui_term" in blob:
        return "TECHNICAL_UI_TERM"
    if "large_file_hard" in blob:
        return "LARGE_FILE_HARD"
    if "many_repair_scripts" in blob or "repair/fix/hotfix" in blob:
        return "MANY_REPAIR_SCRIPTS"
    if "except_without_log" in blob:
        return "EXCEPT_WITHOUT_LOG"
    return item.get("rule") or "UNKNOWN_P1"


def ensure_fresh_p1_analysis(project_root: Path) -> None:
    script = project_root / "scripts/windows/analyze_bys360_quality_10_10_p7_findings.ps1"
    if not script.exists():
        return
    try:
        subprocess.run(
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
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception as exc:
        print(f"BYS360_P13_A2_P1_REFRESH_WARN error={exc}")


def collect_p1_items_from_primary_report(project_root: Path) -> list[dict[str, Any]]:
    # P13-A duplicated counts by merging p1_analysis + clean_report. A2 uses P7/P1 analysis as primary source.
    ensure_fresh_p1_analysis(project_root)
    p1_obj = load_json(project_root / P1_ANALYSIS_REL)
    if p1_obj is None:
        raise SystemExit(f"P1_ANALYSIS_REPORT_NOT_FOUND_OR_INVALID: {project_root / P1_ANALYSIS_REL}")

    raw_items = recursive_findings(p1_obj)
    items: list[dict[str, Any]] = []
    for raw in raw_items:
        item = normalize_finding(raw)
        rule = classify_rule(item)
        # Keep only real P1 findings, not container/summary rows.
        if rule in {"TECHNICAL_UI_TERM", "LARGE_FILE_HARD", "MANY_REPAIR_SCRIPTS", "EXCEPT_WITHOUT_LOG"}:
            item["rule_classified"] = rule
            items.append(item)

    # Strong de-duplication: one finding per rule/path/line/message.
    seen = set()
    deduped = []
    for item in items:
        key = (item["rule_classified"], item["path"], item["line"], item["message"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped


def get_line_count(project_root: Path, rel_path: str) -> int:
    path = project_root / rel_path
    if not path.exists() or not path.is_file():
        return 0
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def build_large_file_plan(project_root: Path, rel_path: str) -> dict[str, Any]:
    line_count = get_line_count(project_root, rel_path)
    plan_map = {
        "app/static/js/bys360_assistant_module.js": {
            "phase": "P14-A",
            "decision": "PLAN_DEDICATED_ASSISTANT_JS_INVENTORY_ONLY",
            "risk": "HIGH",
            "reason": "Asistan ekran zekâsı ve kullanıcı yönlendirme davranışı etkilenebileceği için ilk adım yalnızca envanter olmalı.",
            "next_step": "P14-A assistant JS inventory only.",
        },
        "app/services/settings/effective_menu.py": {
            "phase": "P11-E",
            "decision": "KEEP_WITH_GOVERNANCE_NOTE",
            "risk": "HIGH",
            "reason": "Yetki, kişi bazlı menü görünürlüğü ve DB bağlamı içeriyor; şimdilik bilinçli bırakılmalı.",
            "next_step": "Kod taşıma yok; karar raporunda bilinçli büyük dosya olarak tutulacak.",
        },
        "app/api/mobile/routes.py": {
            "phase": "P11-B",
            "decision": "STOP_AFTER_SAFE_GET_SPLITS",
            "risk": "MEDIUM_HIGH",
            "reason": "Güvenli GET endpointler ayrıldı; kalanlar auth/POST/personel/hassas işlem ağırlıklı.",
            "next_step": "Şimdilik dur; smoke test ve dokümantasyon.",
        },
        "app/api/mobile/performance_routes.py": {
            "phase": "P11-C",
            "decision": "STOP_AFTER_SAFE_GET_SPLITS",
            "risk": "HIGH",
            "reason": "Güvenli GET endpointler ayrıldı; kalanlar puanlama/onay/yayın/score tarafına kaydı.",
            "next_step": "Şimdilik dur; score_submit yerinde kalmalı.",
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


def read_clean_counts(project_root: Path) -> dict[str, int]:
    clean = load_json(project_root / CLEAN_REPORT_REL)
    counts = {"P0": 0, "P1": 0, "P2": 0, "INFO": 0}
    if isinstance(clean, dict):
        for key in ("summary", "counts", "severity_counts"):
            val = clean.get(key)
            if isinstance(val, dict):
                for sev in counts:
                    try:
                        counts[sev] = int(val.get(sev, counts[sev]) or 0)
                    except (TypeError, ValueError) as exc:
                        print(f"BYS360_P13_A2_CLEAN_COUNT_WARN sev={sev} error={exc}")
        # Some clean reports use top-level keys.
        for sev in counts:
            if sev in clean:
                try:
                    counts[sev] = int(clean.get(sev) or counts[sev])
                except (TypeError, ValueError) as exc:
                    print(f"BYS360_P13_A2_CLEAN_TOP_COUNT_WARN sev={sev} error={exc}")
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    print("BYS360_QUALITY_10_10_P13_A2_EFFECTIVE_P1_CLOSURE_MAP_CORRECTED_START")
    print(f"project_root={project_root}")

    p12_b = load_json(project_root / P12_B_REL)
    if p12_b is None:
        raise SystemExit(f"P12_B_REPORT_NOT_FOUND: {project_root / P12_B_REL}")

    items = collect_p1_items_from_primary_report(project_root)
    by_rule = Counter(item["rule_classified"] for item in items)

    clean_counts = read_clean_counts(project_root)
    raw_p1 = int(clean_counts.get("P1") or sum(by_rule.values()))
    technical_count = int(by_rule.get("TECHNICAL_UI_TERM", 0))
    accepted_technical = int(p12_b.get("accepted_false_positive_count") or 0)
    accepted_technical_effective = min(accepted_technical, technical_count)
    manual_review = int(p12_b.get("manual_review_count") or 0)

    effective_p1 = max(0, raw_p1 - accepted_technical_effective)

    large_paths = [item["path"] for item in items if item["rule_classified"] == "LARGE_FILE_HARD" and item["path"]]
    if not large_paths:
        large_paths = [p for p in KNOWN_LARGE_FILES if (project_root / p).exists()]
    large_paths = sorted(set(large_paths), key=lambda p: KNOWN_LARGE_FILES.index(p) if p in KNOWN_LARGE_FILES else 99)
    large_file_plan = [build_large_file_plan(project_root, path) for path in large_paths]

    script_items = [item for item in items if item["rule_classified"] == "MANY_REPAIR_SCRIPTS"]
    except_items = [item for item in items if item["rule_classified"] == "EXCEPT_WITHOUT_LOG"]

    remaining_real_actions = []
    if manual_review:
        remaining_real_actions.append({
            "category": "TECHNICAL_UI_TERM_MANUAL_REVIEW",
            "count": manual_review,
            "decision": "REVIEW_REQUIRED",
        })
    for item in large_file_plan:
        remaining_real_actions.append({
            "category": "LARGE_FILE_HARD",
            "path": item["path"],
            "count": 1,
            "decision": item["decision"],
            "next_step": item["next_step"],
        })
    if script_items:
        remaining_real_actions.append({
            "category": "MANY_REPAIR_SCRIPTS",
            "count": len(script_items),
            "decision": "GOVERNANCE_ARCHIVE_PLAN",
            "next_step": "P13-B/P13-C raporları karar eki olarak tutulacak; silme yapılmayacak.",
        })
    if except_items:
        remaining_real_actions.append({
            "category": "EXCEPT_WITHOUT_LOG",
            "count": len(except_items),
            "decision": "FIX_REQUIRED",
            "next_step": "P13-F3 uygulanmalı veya tekrar kontrol edilmeli.",
        })

    result = {
        "source": "P13-A2 corrected; primary P1 source is P7 analysis report only",
        "raw_clean_counts": clean_counts,
        "raw_p1": raw_p1,
        "p1_rule_summary_corrected": dict(by_rule.most_common()),
        "technical_ui_term_count": technical_count,
        "accepted_technical_ui_false_positive": accepted_technical_effective,
        "accepted_technical_ui_false_positive_reported_by_p12_b": accepted_technical,
        "manual_review_technical_ui": manual_review,
        "effective_p1": effective_p1,
        "large_file_plan": large_file_plan,
        "many_repair_script_items": script_items,
        "except_without_log_items": except_items,
        "remaining_real_actions": remaining_real_actions,
        "recommended_next": {
            "phase": "P14-A",
            "title": "Assistant JS inventory only",
            "reason": "P0 temiz, EXCEPT_WITHOUT_LOG temiz; kalan en büyük bilinçli dosya app/static/js/bys360_assistant_module.js.",
        },
        "safety_strategy": [
            "P13-A2 ham özet için yalnızca P7 P1 analiz raporunu kullanır; clean report ile çift sayım yapmaz.",
            "TECHNICAL_UI_TERM bulguları P12-B karar raporuna göre false positive olarak kabul edilir.",
            "Büyük dosyalarda kod parçalama yapılmaz; sadece faz bazlı karar/enzanter yapılır.",
            "MANY_REPAIR_SCRIPTS için silme yok; arşiv planı/dry-run raporları karar eki olarak tutulur.",
        ],
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p13_a2_effective_p1_closure_map_corrected_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p13_a2_effective_p1_closure_map_corrected_v1.md"
    json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P13-A2 Effective P1 Closure Map — Corrected")
    md.append("")
    md.append(f"- Ham P1: {raw_p1}")
    md.append(f"- Düzeltilmiş P1 kural özeti: {dict(by_rule.most_common())}")
    md.append(f"- Kabul edilen teknik UI false positive: {accepted_technical_effective}")
    md.append(f"- Teknik UI manuel inceleme: {manual_review}")
    md.append(f"- Etkili P1: {effective_p1}")
    md.append("")
    md.append("## Büyük Dosya Planı")
    md.append("")
    for item in large_file_plan:
        md.append(f"- `{item['path']}` ({item['line_count']} satır): {item['decision']} / {item['next_step']}")
    md.append("")
    md.append("## Kalan Gerçek Aksiyonlar")
    md.append("")
    for item in remaining_real_actions:
        if item.get("path"):
            md.append(f"- {item['category']} — `{item['path']}` — {item['decision']}")
        else:
            md.append(f"- {item['category']} — count={item.get('count')} — {item['decision']}")
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
    print("BYS360_QUALITY_10_10_P13_A2_CORRECTED_P1_RULE_SUMMARY")
    for key, count in by_rule.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P13_A2_LARGE_FILE_PLAN")
    for item in large_file_plan:
        print(f"{item['path']} | lines={item['line_count']} | decision={item['decision']} | risk={item['risk']}")
        print(f"    next={item['next_step']}")
    print("BYS360_QUALITY_10_10_P13_A2_REMAINING_REAL_ACTIONS")
    for item in remaining_real_actions:
        print(json.dumps(item, ensure_ascii=False))
    print(f"effective_p1_closure_corrected_json={json_out}")
    print(f"effective_p1_closure_corrected_md={md_out}")
    print("BYS360_QUALITY_10_10_P13_A2_EFFECTIVE_P1_CLOSURE_MAP_CORRECTED_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
