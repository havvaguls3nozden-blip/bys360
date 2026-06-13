from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


TECH_RULE = "TECHNICAL_UI_TERM"
LARGE_RULE = "LARGE_FILE_HARD"
REPAIR_RULE = "MANY_REPAIR_SCRIPTS"


FALSE_POSITIVE_PATH_PREFIXES = (
    "mobile_flutter/bys360_mobile_native/lib/core/network/",
    "mobile_flutter/bys360_mobile_native/lib/core/api/",
    "mobile_flutter/bys360_mobile_native/lib/core/auth/",
    "mobile_flutter/bys360_mobile_native/lib/core/hardening/",
    "mobile_flutter/bys360_mobile_native/lib/core/diagnostics/",
    "mobile_flutter/bys360_mobile_native/lib/core/navigation/",
)

FALSE_POSITIVE_CONTENT_HINTS = (
    "debugShowCheckedModeBanner",
    "debugLogDiagnostics",
    "ApiException",
    "Exception",
    "TimeoutException",
    "SocketException",
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
)

PROJECT_PLAN_RULES = (LARGE_RULE, REPAIR_RULE)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_findings(data: Any, level: str = "P1") -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    level = level.upper()

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            sev = str(x.get("severity") or x.get("level") or x.get("priority") or x.get("rank") or "").upper()
            rule = str(x.get("rule") or x.get("code") or x.get("type") or x.get("category") or x.get("check") or "")
            path = str(x.get("path") or x.get("file") or x.get("filename") or x.get("rel_path") or x.get("relative_path") or "")
            line = x.get("line") or x.get("line_number") or x.get("lineno") or ""
            msg = str(x.get("message") or x.get("detail") or x.get("description") or x.get("reason") or "")
            if sev == level and (path or rule or msg):
                findings.append({
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
    for item in findings:
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
    if not rel:
        return ""
    path = project_root / rel
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if 1 <= line_no <= len(lines):
        return lines[line_no - 1].strip()
    return ""


def decide(item: dict[str, Any], content: str) -> tuple[str, str]:
    rule = item.get("rule", "")
    path = item.get("path", "")
    lower_path = path.lower()

    if rule in PROJECT_PLAN_RULES:
        if rule == LARGE_RULE:
            return "PLANNED_REFACTOR", "Büyük dosya uyarısı aktif hata değil; ayrı refactor planına alınmalı."
        return "PLANNED_PROCESS_IMPROVEMENT", "Repair/fix/hotfix scriptleri aktif hata değil; CI/arşiv sürecine alınmalı."

    if rule == TECH_RULE:
        if any(lower_path.startswith(prefix.lower()) for prefix in FALSE_POSITIVE_PATH_PREFIXES):
            return "ACCEPTED_FALSE_POSITIVE_INTERNAL_CODE", "Mobil çekirdek/ağ/API/yetki/hardening kodu; kullanıcı yüzü metni değil."
        if any(hint in content for hint in FALSE_POSITIVE_CONTENT_HINTS):
            return "ACCEPTED_FALSE_POSITIVE_IDENTIFIER", "Kod anahtarı, route/template değişkeni veya hata sınıfı; kullanıcı metni değil."
        if "import " in content and "api_exception" in content:
            return "ACCEPTED_FALSE_POSITIVE_IMPORT", "Dart import satırı; kullanıcı metni değil."
        return "ACTIVE_REVIEW", "Gerçek kullanıcı metni olabilir; manuel inceleme gerekir."

    return "ACTIVE_REVIEW", "Bilinmeyen P1 türü; manuel inceleme gerekir."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=160)
    parser.add_argument("--fail-on-active", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    clean_report = project_root / "reports" / "quality" / "bys360_quality_10_10_audit_v1_clean.json"
    if not clean_report.exists():
        raise SystemExit(f"REPORT_NOT_FOUND: {clean_report}")

    findings = collect_findings(load_json(clean_report), "P1")
    rows = []
    for item in findings:
        content = read_line(project_root, item["path"], item["line"])
        decision, reason = decide(item, content)
        rows.append({**item, "content": content, "decision": decision, "reason": reason})

    by_decision = Counter(row["decision"] for row in rows)
    active_rows = [row for row in rows if row["decision"] == "ACTIVE_REVIEW"]
    accepted_false_positive = [row for row in rows if row["decision"].startswith("ACCEPTED_FALSE_POSITIVE")]
    planned_rows = [row for row in rows if row["decision"].startswith("PLANNED_")]

    print("BYS360_QUALITY_10_10_P10_2_FINAL_P1_DECISION_START")
    print(f"project_root={project_root}")
    print(f"raw_p1={len(rows)}")
    print(f"accepted_false_positive={len(accepted_false_positive)}")
    print(f"planned_p1_items={len(planned_rows)}")
    print(f"active_review_items={len(active_rows)}")

    print("BYS360_QUALITY_10_10_P10_2_DECISION_SUMMARY")
    for key, count in by_decision.most_common():
        print(f"{count:>4} | {key}")

    print("BYS360_QUALITY_10_10_P10_2_ACTIVE_REVIEW")
    for i, row in enumerate(active_rows[: args.limit], 1):
        print(f"[{i}] path={row['path']} line={row['line']} rule={row['rule']}")
        print(f"    reason={row['reason']}")
        print(f"    content={row['content']}")

    output_dir = project_root / "reports" / "quality"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_json = output_dir / "bys360_quality_10_10_p10_2_final_p1_decision_v1.json"
    output_md = output_dir / "bys360_quality_10_10_p10_2_final_p1_decision_v1.md"

    output_json.write_text(json.dumps({
        "raw_p1": len(rows),
        "accepted_false_positive": len(accepted_false_positive),
        "planned_p1_items": len(planned_rows),
        "active_review_items": len(active_rows),
        "by_decision": dict(by_decision.most_common()),
        "rows": rows,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# BYS360 Quality 10/10 P10.2 Final P1 Decision",
        "",
        f"- Raw P1: {len(rows)}",
        f"- Accepted false-positive: {len(accepted_false_positive)}",
        f"- Planned refactor/process items: {len(planned_rows)}",
        f"- Active review items: {len(active_rows)}",
        "",
        "## Decision Summary",
        "",
    ]
    for key, count in by_decision.most_common():
        md_lines.append(f"- {key}: {count}")
    md_lines.extend(["", "## Active Review Items", ""])
    if active_rows:
        for row in active_rows:
            md_lines.append(f"- `{row['path']}:{row['line']}` `{row['rule']}` — {row['content']}")
    else:
        md_lines.append("Aktif P1 inceleme kaydı kalmadı. Kalanlar false-positive veya planlanmış refactor/süreç maddesidir.")
    output_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"decision_report_json={output_json}")
    print(f"decision_report_md={output_md}")
    print("BYS360_QUALITY_10_10_P10_2_FINAL_P1_DECISION_OK")

    if args.fail_on_active and active_rows:
        raise SystemExit("ACTIVE_REVIEW_ITEMS_FOUND")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
