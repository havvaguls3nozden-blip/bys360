from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


TECH_RULE = "TECHNICAL_UI_TERM"
LARGE_RULE = "LARGE_FILE_HARD"
REPAIR_RULE = "MANY_REPAIR_SCRIPTS"


INTERNAL_CODE_PATTERNS = [
    "mobile_flutter/bys360_mobile_native/lib/core/network/",
    "mobile_flutter/bys360_mobile_native/lib/core/api/",
    "mobile_flutter/bys360_mobile_native/lib/core/auth/",
    "mobile_flutter/bys360_mobile_native/lib/core/hardening/",
    "mobile_flutter/bys360_mobile_native/lib/core/diagnostics/",
    "mobile_flutter/bys360_mobile_native/lib/core/navigation/",
    "mobile_flutter/bys360_mobile_native/test/",
]

FALSE_POSITIVE_LINE_HINTS = [
    "ApiException",
    "Exception",
    "TimeoutException",
    "SocketException",
    "debugShowCheckedModeBanner",
    "debugLogDiagnostics",
    "request.endpoint",
    "safe_url_for(item.endpoint",
    "safe_url_for(card.endpoint",
    "safe_url_for(link.endpoint",
    "safe_url_for(step.endpoint",
    "endpoint_checks",
    "endpoint_ok",
    "exception_type",
    "attendance_type_label(row.exception_type)",
    "data-ai-reminder-endpoint",
]

STILL_REVIEW_LINE_HINTS = [
    "İşlem tamamlanamadı",
    "beklenen formatta",
    "Demo ön izleme",
    "yetkiniz bulunmamaktadır",
    "Mobil oturum anahtarı",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_findings(data: Any, level: str = "P1") -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    level = level.upper()

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            sev = str(x.get("severity") or x.get("level") or x.get("priority") or x.get("rank") or "").upper()
            rule = str(x.get("rule") or x.get("code") or x.get("type") or x.get("category") or x.get("check") or "")
            path = str(x.get("path") or x.get("file") or x.get("filename") or x.get("rel_path") or x.get("relative_path") or "")
            line = x.get("line") or x.get("line_number") or x.get("lineno") or ""
            msg = str(x.get("message") or x.get("detail") or x.get("description") or x.get("reason") or "")
            if sev == level and (path or rule or msg):
                out.append({
                    "severity": sev,
                    "rule": rule,
                    "path": path.replace("\\", "/").lstrip("./"),
                    "line": line,
                    "message": msg,
                })
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(data)

    seen = set()
    uniq = []
    for item in out:
        key = (item["rule"], item["path"], str(item["line"]), item["message"])
        if key not in seen:
            seen.add(key)
            uniq.append(item)
    return uniq


def read_line(project_root: Path, rel: str, line: Any) -> str:
    try:
        line_no = int(line)
    except Exception:
        return ""
    target = project_root / rel
    if not target.exists():
        return ""
    lines = target.read_text(encoding="utf-8", errors="ignore").splitlines()
    if line_no < 1 or line_no > len(lines):
        return ""
    return lines[line_no - 1].strip()


def classify(item: dict[str, Any], content: str) -> tuple[str, str]:
    rule = item["rule"]
    path = item["path"]
    lower_path = path.lower()

    if rule == LARGE_RULE:
        return "REFACTOR_PLAN", "Büyük dosya; doğrudan patch değil, modül parçalama planı gerekir."
    if rule == REPAIR_RULE:
        return "PROCESS_PLAN", "Repair/hotfix scriptleri arşiv ve CI planına alınmalı."
    if rule != TECH_RULE:
        return "REVIEW", "Bilinmeyen P1 türü; ayrıca incelenmeli."

    if any(p.lower() in lower_path for p in INTERNAL_CODE_PATTERNS):
        return "INTERNAL_CODE_FALSE_POSITIVE", "Mobil çekirdek/API/ağ/yetki/hardening kodu; kullanıcı ekranı metni değil."

    if any(hint in content for hint in FALSE_POSITIVE_LINE_HINTS):
        return "LIKELY_FALSE_POSITIVE", "Kod anahtarı, route endpoint adı veya dahili template değişkeni; kullanıcı metni değil."

    if any(hint in content for hint in STILL_REVIEW_LINE_HINTS):
        return "TEXT_REVIEW", "Kullanıcıya dönebilecek metin olabilir; sadeleştirme gözden geçirilmeli."

    if path.startswith("app/templates/hr_attendance.html") and "exception_type" in content:
        return "DOMAIN_TERM_REVIEW", "Devam/izin istisna türü alanı; teknik değil, alan adı olabilir."

    return "TEXT_OR_SCOPE_REVIEW", "Kullanıcı metni mi yoksa kod anahtarı mı netleştirilmeli."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=160)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    clean_report = project_root / "reports" / "quality" / "bys360_quality_10_10_audit_v1_clean.json"
    if not clean_report.exists():
        raise SystemExit(f"REPORT_NOT_FOUND: {clean_report}")

    findings = collect_findings(load_json(clean_report), "P1")
    rows = []

    for item in findings:
        content = read_line(project_root, item["path"], item["line"])
        decision, reason = classify(item, content)
        rows.append({**item, "content": content, "decision": decision, "reason": reason})

    by_rule = Counter(row["rule"] for row in rows)
    by_decision = Counter(row["decision"] for row in rows)
    by_path = Counter(row["path"] for row in rows)

    print("BYS360_QUALITY_10_10_P10_REMAINING_P1_TRIAGE_START")
    print(f"project_root={project_root}")
    print(f"remaining_p1={len(rows)}")

    print("BYS360_QUALITY_10_10_P10_RULE_SUMMARY")
    for key, count in by_rule.most_common():
        print(f"{count:>4} | {key}")

    print("BYS360_QUALITY_10_10_P10_DECISION_SUMMARY")
    for key, count in by_decision.most_common():
        print(f"{count:>4} | {key}")

    print("BYS360_QUALITY_10_10_P10_TOP_PATHS")
    for key, count in by_path.most_common(80):
        print(f"{count:>4} | {key}")

    print("BYS360_QUALITY_10_10_P10_REVIEW_FIRST")
    review_kinds = {"TEXT_REVIEW", "TEXT_OR_SCOPE_REVIEW", "DOMAIN_TERM_REVIEW"}
    shown = 0
    for i, row in enumerate(rows, 1):
        if row["decision"] in review_kinds:
            shown += 1
            print(f"[{shown}] path={row['path']} line={row['line']} rule={row['rule']} decision={row['decision']}")
            print(f"    reason={row['reason']}")
            print(f"    content={row['content']}")
            if shown >= args.limit:
                break

    output = project_root / "reports" / "quality" / "bys360_quality_10_10_p10_remaining_p1_triage_v1.json"
    output.write_text(json.dumps({
        "total": len(rows),
        "by_rule": dict(by_rule.most_common()),
        "by_decision": dict(by_decision.most_common()),
        "by_path": dict(by_path.most_common()),
        "rows": rows,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"triage_report={output}")
    print("BYS360_QUALITY_10_10_P10_REMAINING_P1_TRIAGE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
