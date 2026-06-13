from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


A1_REPORT_REL = "reports/quality/bys360_quality_10_10_p12_a1_technical_ui_term_inventory_fix_v1.json"
CLEAN_REPORT_REL = "reports/quality/bys360_quality_10_10_audit_v1_clean.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def recursive_findings(obj: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        # Handles common finding shapes.
        if any(k in obj for k in ("rule", "rule_id", "severity", "level", "path", "file", "message")):
            out.append(obj)
        for value in obj.values():
            out.extend(recursive_findings(value))
    elif isinstance(obj, list):
        for item in obj:
            out.extend(recursive_findings(item))
    return out


def get_any(obj: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in obj:
            return obj.get(key)
    lower_map = {str(k).lower(): v for k, v in obj.items()}
    for key in keys:
        if key.lower() in lower_map:
            return lower_map.get(key.lower())
    return None


def normalize_path(value: Any) -> str:
    return str(value or "").replace("\\", "/").strip()


def classify_decision(item: dict[str, Any]) -> tuple[str, str, str]:
    path = normalize_path(item.get("path"))
    line_text = str(item.get("line_text") or "").strip()
    decision = str(item.get("decision") or "")
    terms = item.get("terms") or []
    low_path = path.lower()
    low_line = line_text.lower()

    # Import and contract paths are internal code references, not UI copy.
    if line_text.startswith("import "):
        return (
            "ACCEPTED_FALSE_POSITIVE_IMPORT",
            "İçe aktarma satırı kullanıcıya görünen metin değildir.",
            "no_code_change",
        )

    if "core/api/" in low_path and ("endpoint" in low_line or "/api/" in low_line):
        return (
            "ACCEPTED_FALSE_POSITIVE_ENDPOINT_CONTRACT",
            "Mobil API sözleşme sabitleri ve URL path değerleri teknik olarak korunmalıdır; kullanıcı metni değildir.",
            "no_code_change",
        )

    if "api_exception.dart" in low_path or "api_client.dart" in low_path:
        return (
            "ACCEPTED_FALSE_POSITIVE_EXCEPTION_CODE",
            "ApiException/ApiClient kod sınıfı ve hata yakalama akışı kullanıcı metni değildir; sınıf/akış adı değiştirilmemelidir.",
            "no_code_change",
        )

    if "auth_controller.dart" in low_path and "ApiException" in line_text:
        return (
            "ACCEPTED_FALSE_POSITIVE_EXCEPTION_CODE",
            "Dart hata sınıfı kullanımıdır; içindeki kullanıcı mesajı zaten Türkçedir.",
            "no_code_change",
        )

    if "performance_scoring_form_screen.dart" in low_path and "ApiException" in line_text:
        return (
            "ACCEPTED_FALSE_POSITIVE_SANITIZER",
            "Bu satır teknik öneki kullanıcıya göstermemek için temizleyen koruma satırıdır; görünür metin değildir.",
            "no_code_change",
        )

    if "debugshowcheckedmodebanner" in low_line or "debuglogdiagnostics" in low_line:
        return (
            "ACCEPTED_FALSE_POSITIVE_DEBUG_FLAG",
            "Flutter geliştirme bayrağıdır; kullanıcıya görünen metin değildir.",
            "no_code_change",
        )

    if "stack" in low_line or "socketexception" in low_line or "timeoutexception" in low_line or "error is" in low_line:
        return (
            "ACCEPTED_FALSE_POSITIVE_ERROR_HANDLING_CODE",
            "Hata yakalama/izleme kodudur; kullanıcıya görünen metin değildir.",
            "no_code_change",
        )

    if path.startswith("app/templates/"):
        # Template routing/internal variables are not UI copy.
        if (
            "request.endpoint" in line_text
            or "safe_url_for(" in line_text
            or "endpoint_ok" in line_text
            or "endpoint_checks" in line_text
            or "data-ai-reminder-endpoint" in line_text
            or "data-role=" in line_text
            or "exception_type" in line_text
        ):
            return (
                "ACCEPTED_FALSE_POSITIVE_TEMPLATE_INTERNAL_VARIABLE",
                "Şablon içi endpoint/data/alan değişkenidir; ekranda teknik metin olarak görünmez veya alan adı değiştirilemez.",
                "no_code_change",
            )

    if "mobile_real_api_contract.dart" in low_path:
        return (
            "ACCEPTED_FALSE_POSITIVE_ENDPOINT_CONTRACT",
            "Mobil gerçek API sözleşme listesi kod içi doğrulama bilgisidir.",
            "no_code_change",
        )

    if "support_survey_mobile_p1_contract.dart" in low_path:
        return (
            "ACCEPTED_FALSE_POSITIVE_ENDPOINT_CONTRACT",
            "Destek/anket API sözleşme sabiti kod içidir; URL bozulmamalıdır.",
            "no_code_change",
        )

    if decision in {"REVIEW_DART_CONTEXT", "REVIEW_DART_VISIBLE_TEXT", "REVIEW_TEMPLATE_VISIBLE_TEXT", "REVIEW_TEMPLATE_CONTEXT"}:
        # If we got here, require manual review instead of patching.
        return (
            "MANUAL_REVIEW_REQUIRED",
            "Güvenli otomatik değişiklik için yeterli bağlam yok; kod sembolü veya kullanıcı metni ayrımı elle doğrulanmalı.",
            "manual_review",
        )

    if "FALSE_POSITIVE" in decision or decision == "LIKELY_CODE_FALSE_POSITIVE":
        return (
            "ACCEPTED_FALSE_POSITIVE_CODE_CONTEXT",
            "Kod bağlamı; kullanıcıya görünen metin değildir.",
            "no_code_change",
        )

    return (
        "MANUAL_REVIEW_REQUIRED",
        "Bağlam belirsiz; otomatik patch uygulanmadı.",
        "manual_review",
    )


def summarize_clean_report(clean: Any) -> dict[str, int]:
    findings = recursive_findings(clean)
    counts = Counter()
    for item in findings:
        severity = str(get_any(item, ["severity", "level", "priority"]) or "").upper()
        rule = str(get_any(item, ["rule", "rule_id", "code", "name"]) or "")
        # Avoid counting container nodes.
        if severity in {"P0", "P1", "P2", "INFO"}:
            counts[severity] += 1
        elif rule:
            # Some clean report structures group by keys elsewhere, not each item.
            pass

    # Fallback: try summary keys.
    if not counts:
        if isinstance(clean, dict):
            for key in ("summary", "counts", "severity_counts"):
                val = clean.get(key)
                if isinstance(val, dict):
                    for sev in ("P0", "P1", "P2", "INFO"):
                        if sev in val:
                            try:
                                counts[sev] = int(val[sev])
                            except Exception as exc:
                                print("BYS360_P12_B_SUMMARY_COUNT_PARSE_WARN line=182 error=" + repr(exc))

    return {sev: int(counts.get(sev, 0)) for sev in ("P0", "P1", "P2", "INFO")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    a1_path = project_root / A1_REPORT_REL
    clean_path = project_root / CLEAN_REPORT_REL

    print("BYS360_QUALITY_10_10_P12_B_TECHNICAL_UI_TERM_DECISION_START")
    print(f"project_root={project_root}")
    print(f"a1_report={a1_path}")
    print(f"clean_report={clean_path}")

    if not a1_path.exists():
        raise SystemExit(f"A1_REPORT_NOT_FOUND: {a1_path}")

    a1 = load_json(a1_path)
    all_items = list(a1.get("all_items") or [])
    if not all_items:
        # Support alternate key names.
        all_items = list(a1.get("p12_b_visible_text_candidates") or [])
        all_items += list(a1.get("review_candidates") or [])
        all_items += list(a1.get("false_positive_candidates") or [])

    decisions = []
    for item in all_items:
        decision_code, reason, action = classify_decision(item)
        decisions.append({
            "path": item.get("path"),
            "line": item.get("line"),
            "line_text": item.get("line_text"),
            "terms": item.get("terms") or [],
            "a1_decision": item.get("decision"),
            "p12_b_decision": decision_code,
            "reason": reason,
            "action": action,
        })

    by_decision = Counter(d["p12_b_decision"] for d in decisions)
    by_action = Counter(d["action"] for d in decisions)
    by_path = Counter(str(d["path"]) for d in decisions)

    accepted_false_positive = [
        d for d in decisions
        if str(d["p12_b_decision"]).startswith("ACCEPTED_FALSE_POSITIVE")
    ]
    manual_review = [d for d in decisions if d["action"] == "manual_review"]

    clean_counts = {}
    if clean_path.exists():
        clean_counts = summarize_clean_report(load_json(clean_path))

    raw_p1 = int(clean_counts.get("P1", 0) or 0)
    accepted_count = len(accepted_false_positive)
    # TECHNICAL_UI_TERM count is known from A1; only estimate effective governance P1.
    effective_p1_estimate = max(0, raw_p1 - accepted_count) if raw_p1 else None

    result = {
        "a1_report": A1_REPORT_REL,
        "clean_report": CLEAN_REPORT_REL if clean_path.exists() else None,
        "raw_clean_counts": clean_counts,
        "technical_ui_term_items": len(decisions),
        "accepted_false_positive_count": accepted_count,
        "manual_review_count": len(manual_review),
        "by_decision": dict(by_decision.most_common()),
        "by_action": dict(by_action.most_common()),
        "by_path": dict(by_path.most_common()),
        "effective_p1_estimate_after_accepted_technical_ui_terms": effective_p1_estimate,
        "decisions": decisions,
        "manual_review_items": manual_review,
        "accepted_false_positive_items": accepted_false_positive,
        "safety_strategy": [
            "Bu paket uygulama kodunu değiştirmez.",
            "Endpoint URL’leri, importlar, ApiException/ApiClient sınıfları, debug bayrakları ve Jinja endpoint değişkenleri kullanıcı metni değildir.",
            "Bu bulgular kalite raporunda kabul edilen false positive olarak ayrılmalıdır.",
            "Manuel inceleme listesi boş değilse uygulama kodu patchlenmeden önce satır bazında kontrol yapılmalıdır.",
            "P12-B sonrası gerçek kod patch’i yalnızca kullanıcıya açık Türkçe metinlerde yapılabilir.",
        ],
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p12_b_technical_ui_term_decision_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p12_b_technical_ui_term_decision_v1.md"
    json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P12-B Technical UI Term Decision Report")
    md.append("")
    md.append(f"- Teknik UI bulgusu: {len(decisions)}")
    md.append(f"- Kabul edilen false positive: {accepted_count}")
    md.append(f"- Manuel inceleme: {len(manual_review)}")
    if clean_counts:
        md.append(f"- Ham clean audit sayımları: {clean_counts}")
    if effective_p1_estimate is not None:
        md.append(f"- Teknik UI false positive kararları sonrası etkili P1 tahmini: {effective_p1_estimate}")
    md.append("")
    md.append("## Karar Özeti")
    md.append("")
    for key, count in by_decision.most_common():
        md.append(f"- {key}: {count}")
    md.append("")
    md.append("## Kabul Edilen False Positive Örnekleri")
    md.append("")
    for item in accepted_false_positive[:120]:
        md.append(f"- `{item['path']}`:{item['line']} — {item['p12_b_decision']} — `{str(item['line_text']).strip()[:180]}`")
    md.append("")
    md.append("## Manuel İnceleme Gerektirenler")
    md.append("")
    if manual_review:
        for item in manual_review[:120]:
            md.append(f"- `{item['path']}`:{item['line']} — {item['p12_b_decision']} — `{str(item['line_text']).strip()[:180]}`")
    else:
        md.append("- Manuel inceleme gerektiren teknik UI metni kalmadı.")
    md.append("")
    md.append("## Güvenlik Stratejisi")
    md.append("")
    for item in result["safety_strategy"]:
        md.append(f"- {item}")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"technical_ui_term_items={len(decisions)}")
    print(f"accepted_false_positive_count={accepted_count}")
    print(f"manual_review_count={len(manual_review)}")
    if clean_counts:
        print("BYS360_QUALITY_10_10_P12_B_RAW_CLEAN_COUNTS")
        for key in ("P0", "P1", "P2", "INFO"):
            print(f"{key}={clean_counts.get(key, 0)}")
    if effective_p1_estimate is not None:
        print(f"effective_p1_estimate_after_accepted_technical_ui_terms={effective_p1_estimate}")
    print("BYS360_QUALITY_10_10_P12_B_DECISION_SUMMARY")
    for key, count in by_decision.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P12_B_MANUAL_REVIEW_ITEMS")
    for item in manual_review[:200]:
        print(f"{item['path']}:{item['line']} | {item['p12_b_decision']} | {item['reason']}")
        print(f"    {str(item['line_text']).strip()[:220]}")
    print(f"technical_ui_decision_json={json_out}")
    print(f"technical_ui_decision_md={md_out}")
    print("BYS360_QUALITY_10_10_P12_B_TECHNICAL_UI_TERM_DECISION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
