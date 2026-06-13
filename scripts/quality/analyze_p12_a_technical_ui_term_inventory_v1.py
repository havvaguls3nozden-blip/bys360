from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_REPORT_REL = "reports/quality/bys360_quality_10_10_audit_v1_clean.json"

TECHNICAL_TERMS = {
    "api": "sistem bağlantısı / veri bağlantısı",
    "endpoint": "erişim noktası / işlem adresi",
    "request": "işlem talebi",
    "response": "sistem yanıtı",
    "token": "güvenli oturum bilgisi",
    "jwt": "güvenli oturum doğrulaması",
    "session": "oturum",
    "cache": "geçici kayıt",
    "debug": "kontrol bilgisi",
    "exception": "işlem hatası",
    "stack": "hata ayrıntısı",
    "trace": "iz kaydı",
    "crash": "beklenmeyen kapanma",
    "timeout": "yanıt süresi aşıldı",
    "server": "sunucu",
    "client": "istemci / kullanıcı uygulaması",
    "http": "bağlantı",
    "https": "güvenli bağlantı",
    "json": "veri yanıtı",
    "url": "bağlantı adresi",
    "uri": "bağlantı adresi",
    "backend": "arka plan sistemi",
    "frontend": "arayüz",
    "build": "sürüm hazırlığı",
    "release": "yayın sürümü",
    "mock": "örnek veri",
    "fallback": "yedek akış",
    "service": "hizmet bileşeni",
    "provider": "sağlayıcı",
    "contract": "veri sözleşmesi",
    "controller": "denetleyici",
    "router": "yönlendirici",
    "route": "ekran yolu",
    "database": "veritabanı",
    "db": "veritabanı",
    "log": "işlem kaydı",
    "sync": "eşitleme",
    "async": "zaman uyumsuz işlem",
    "network": "ağ bağlantısı",
    "status code": "durum kodu",
    "null": "boş değer",
    "socket": "bağlantı kanalı",
    "payload": "veri paketi",
    "error": "hata",
}

CODE_CONTEXT_PATTERNS = [
    r"^\s*import\s+",
    r"^\s*from\s+",
    r"^\s*class\s+",
    r"^\s*def\s+",
    r"^\s*function\s+",
    r"^\s*const\s+\w+\s*=",
    r"^\s*final\s+\w+\s*=",
    r"^\s*var\s+\w+\s*=",
    r"^\s*static\s+",
    r"^\s*Future<",
    r"^\s*Map<",
    r"^\s*List<",
    r"^\s*@",
    r"^\s*//",
    r"^\s*#",
]

HTML_VISIBLE_HINTS = [
    "<span", "<div", "<p", "<button", "<label", "<small", "<h1", "<h2", "<h3", "<h4",
    "<td", "<th", "title=", "aria-label=", "placeholder="
]

DART_VISIBLE_HINTS = [
    "Text(", "SnackBar", "content:", "label:", "hintText:", "errorText:", "helperText:",
    "title:", "subtitle:", "Tooltip", "AlertDialog"
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def recursive_findings(obj: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        if "rule" in obj and ("path" in obj or "file" in obj or "message" in obj):
            out.append(obj)
        for value in obj.values():
            out.extend(recursive_findings(value))
    elif isinstance(obj, list):
        for item in obj:
            out.extend(recursive_findings(item))
    return out


def normalize_path(value: Any) -> str:
    return str(value or "").replace("\\", "/").strip()


def get_line_text(project_root: Path, rel_path: str, line_no: int) -> str:
    if not rel_path or not line_no:
        return ""
    path = project_root / rel_path
    if not path.exists() or not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if 1 <= line_no <= len(lines):
        return lines[line_no - 1]
    return ""


def get_context(project_root: Path, rel_path: str, line_no: int, radius: int = 2) -> list[dict[str, Any]]:
    path = project_root / rel_path
    if not path.exists() or not path.is_file() or not line_no:
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    start = max(1, line_no - radius)
    end = min(len(lines), line_no + radius)
    return [{"line": i, "text": lines[i - 1]} for i in range(start, end + 1)]


def extract_terms(text: str) -> list[str]:
    low = text.lower()
    found = []
    for term in TECHNICAL_TERMS:
        if re.search(r"\b" + re.escape(term.lower()) + r"\b", low):
            found.append(term)
    return sorted(found)


def looks_code_context(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in CODE_CONTEXT_PATTERNS)


def classify_candidate(rel_path: str, line_text: str, message: str) -> tuple[str, str]:
    lower_path = rel_path.lower()
    text = line_text.strip()
    low = text.lower()

    if rel_path == "scripts" or lower_path.startswith("scripts"):
        return "PROCESS_ITEM", "Script envanteri / arşiv planı konusu; UI metni değildir."

    if "mobile_flutter/" in lower_path and lower_path.endswith(".dart"):
        if any(h in text for h in DART_VISIBLE_HINTS) or re.search(r"['\"][^'\"]+['\"]", text):
            if extract_terms(text):
                return "REVIEW_DART_VISIBLE_TEXT", "Dart içinde kullanıcıya görünen metin olabilir; P12-B için aday."
        if looks_code_context(text):
            return "LIKELY_CODE_FALSE_POSITIVE", "Kod/import/sınıf/sabit satırı olabilir; kullanıcıya görünmeyebilir."
        return "REVIEW_DART_CONTEXT", "Dart satırı; görünür metin mi kod içi mi kontrol edilmeli."

    if lower_path.endswith((".html", ".jinja", ".jinja2")) or "templates/" in lower_path:
        if any(h in low for h in HTML_VISIBLE_HINTS) or "{{" in text or "{%" in text:
            return "REVIEW_TEMPLATE_VISIBLE_TEXT", "Şablon içinde kullanıcıya görünen metin olabilir; P12-B için aday."
        return "REVIEW_TEMPLATE_CONTEXT", "Şablon satırı; görünür metin mi kontrol edilmeli."

    if lower_path.endswith((".py", ".js")):
        if re.search(r"['\"][^'\"]+['\"]", text) and not looks_code_context(text):
            return "REVIEW_STRING_LITERAL", "Kod içinde kullanıcıya gösterilen string olabilir; dikkatli kontrol edilmeli."
        return "LIKELY_CODE_FALSE_POSITIVE", "Kod içi teknik terim olabilir; otomatik metin düzeltmesi önerilmez."

    return "REVIEW_UNKNOWN", "Bağlam belirsiz; elle incelenmeli."


def suggest_replacements(terms: list[str]) -> list[dict[str, str]]:
    return [{"term": term, "suggestion": TECHNICAL_TERMS.get(term, "kurumsal Türkçe karşılık")} for term in terms]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--report", default=DEFAULT_REPORT_REL)
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    report_path = project_root / args.report

    print("BYS360_QUALITY_10_10_P12_A_TECHNICAL_UI_TERM_INVENTORY_START")
    print(f"project_root={project_root}")
    print(f"report={report_path}")

    if not report_path.exists():
        raise SystemExit(f"REPORT_NOT_FOUND: {report_path}")

    all_findings = recursive_findings(load_json(report_path))

    technical = []
    for finding in all_findings:
        rule = str(finding.get("rule") or finding.get("rule_id") or "").strip()
        if rule != "TECHNICAL_UI_TERM":
            continue

        rel_path = normalize_path(finding.get("path") or finding.get("file"))
        try:
            line_no = int(finding.get("line") or finding.get("line_number") or 0)
        except Exception:
            line_no = 0

        message = str(finding.get("message") or "")
        line_text = get_line_text(project_root, rel_path, line_no)
        terms = extract_terms(line_text + " " + message)
        decision, reason = classify_candidate(rel_path, line_text, message)

        technical.append({
            "path": rel_path,
            "line": line_no,
            "rule": rule,
            "message": message,
            "line_text": line_text,
            "terms": terms,
            "suggestions": suggest_replacements(terms),
            "decision": decision,
            "reason": reason,
            "context": get_context(project_root, rel_path, line_no),
        })

    by_path = Counter(item["path"] for item in technical)
    by_decision = Counter(item["decision"] for item in technical)
    by_term = Counter(term for item in technical for term in item["terms"])

    p12_b_candidates = [
        item for item in technical
        if item["decision"] in {"REVIEW_DART_VISIBLE_TEXT", "REVIEW_TEMPLATE_VISIBLE_TEXT", "REVIEW_STRING_LITERAL"}
    ]
    review_candidates = [
        item for item in technical
        if item["decision"].startswith("REVIEW") and item not in p12_b_candidates
    ]
    false_positive_candidates = [
        item for item in technical
        if "FALSE_POSITIVE" in item["decision"] or item["decision"] == "LIKELY_CODE_FALSE_POSITIVE"
    ]

    result = {
        "source_report": args.report,
        "technical_ui_term_count": len(technical),
        "by_path": dict(by_path.most_common()),
        "by_decision": dict(by_decision.most_common()),
        "by_term": dict(by_term.most_common()),
        "p12_b_visible_text_candidates": p12_b_candidates,
        "review_candidates": review_candidates,
        "false_positive_candidates": false_positive_candidates,
        "all_items": technical,
        "next_step": "P12-B: sadece kullanıcıya görünen string literal veya HTML görünür metinleri için patch üret.",
        "safety_strategy": [
            "Kod sembolleri, importlar, class/function adları ve contract/controller/api_client gibi teknik dosya isimleri otomatik değiştirilmemeli.",
            "Sadece kullanıcıya görünen string literal veya HTML görünür metinleri çevrilmeli.",
            "Dart dosyalarında sınıf, provider, controller, contract, API client gibi mimari isimler korunmalı.",
            "Şablonlarda route/url/id/name/data-* alanlarına dokunulmamalı.",
            "Her patch sonrası compileall, Flutter analyze/build ve kalite audit çalıştırılmalı.",
        ],
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p12_a_technical_ui_term_inventory_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p12_a_technical_ui_term_inventory_v1.md"

    json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P12-A Technical UI Term Inventory")
    md.append("")
    md.append(f"- Kaynak rapor: `{args.report}`")
    md.append(f"- TECHNICAL_UI_TERM toplamı: {len(technical)}")
    md.append("")
    md.append("## Karar Özeti")
    md.append("")
    for key, count in by_decision.most_common():
        md.append(f"- {key}: {count}")
    md.append("")
    md.append("## Dosya Özeti")
    md.append("")
    for key, count in by_path.most_common():
        md.append(f"- `{key}`: {count}")
    md.append("")
    md.append("## Terim Özeti")
    md.append("")
    if by_term:
        for key, count in by_term.most_common():
            md.append(f"- `{key}`: {count} → {TECHNICAL_TERMS.get(key, '-')}")
    else:
        md.append("- Satırlarda açık teknik terim yakalanmadı; kalite raporu muhtemelen dosya/satır bazlı sezgisel işaretleme yapmış.")
    md.append("")
    md.append("## P12-B İçin Görünür Metin Adayları")
    md.append("")
    if p12_b_candidates:
        for item in p12_b_candidates[:120]:
            md.append(f"- `{item['path']}`:{item['line']} — {item['decision']} — `{item['line_text'].strip()[:180]}`")
    else:
        md.append("- Doğrudan güvenli görünür metin adayı bulunmadı.")
    md.append("")
    md.append("## Elle İnceleme Adayları")
    md.append("")
    for item in review_candidates[:120]:
        md.append(f"- `{item['path']}`:{item['line']} — {item['decision']} — `{item['line_text'].strip()[:180]}`")
    md.append("")
    md.append("## Muhtemel False Positive / Kod İçi")
    md.append("")
    for item in false_positive_candidates[:120]:
        md.append(f"- `{item['path']}`:{item['line']} — {item['decision']} — `{item['line_text'].strip()[:180]}`")
    md.append("")
    md.append("## Güvenlik Stratejisi")
    md.append("")
    for item in result["safety_strategy"]:
        md.append(f"- {item}")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"technical_ui_term_count={len(technical)}")
    print("BYS360_QUALITY_10_10_P12_A_DECISION_SUMMARY")
    for key, count in by_decision.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P12_A_PATH_SUMMARY")
    for key, count in by_path.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P12_A_TERM_SUMMARY")
    for key, count in by_term.most_common():
        print(f"{count:>4} | {key} => {TECHNICAL_TERMS.get(key, '-')}")
    print("BYS360_QUALITY_10_10_P12_A_P12_B_VISIBLE_TEXT_CANDIDATES")
    for item in p12_b_candidates[:args.limit]:
        print(f"{item['path']}:{item['line']} | {item['decision']} | terms={','.join(item['terms']) or '-'}")
        print(f"    {item['line_text'].strip()[:220]}")
    print("BYS360_QUALITY_10_10_P12_A_REVIEW_CANDIDATES")
    for item in review_candidates[:args.limit]:
        print(f"{item['path']}:{item['line']} | {item['decision']} | terms={','.join(item['terms']) or '-'}")
        print(f"    {item['line_text'].strip()[:220]}")
    print("BYS360_QUALITY_10_10_P12_A_FALSE_POSITIVE_CANDIDATES")
    for item in false_positive_candidates[:args.limit]:
        print(f"{item['path']}:{item['line']} | {item['decision']} | terms={','.join(item['terms']) or '-'}")
        print(f"    {item['line_text'].strip()[:220]}")
    print(f"technical_ui_inventory_json={json_out}")
    print(f"technical_ui_inventory_md={md_out}")
    print("BYS360_QUALITY_10_10_P12_A_TECHNICAL_UI_TERM_INVENTORY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
