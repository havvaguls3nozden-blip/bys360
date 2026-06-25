from pathlib import Path
from datetime import datetime
import json
import subprocess
import os
import re
from collections import Counter, defaultdict

ROOT = Path(".").resolve()

OUT_JSON = Path("reports/quality/BYS360_A11A_WARNING_AUDIT.json")
OUT_MD = Path("reports/quality/BYS360_A11A_WARNING_AUDIT.md")
RAW_TXT = Path("reports/quality/BYS360_A11A_WARNING_AUDIT_RAW_PYTEST.txt")

def run_cmd(cmd, timeout=1800):
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="ignore",
        env={
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONWARNINGS": "default",
            "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS": "1",
        },
        timeout=timeout,
    )
    return {
        "cmd": " ".join(map(str, cmd)),
        "returncode": proc.returncode,
        "stdout": proc.stdout or "",
        "stderr": proc.stderr or "",
        "combined": (proc.stdout or "") + "\n" + (proc.stderr or ""),
    }

def parse_pytest_summary(text: str):
    summary = {}
    for num, key in re.findall(r"(\d+)\s+(failed|passed|error|errors|skipped|deselected|warnings|warning)", text or ""):
        key = key.lower()
        if key == "error":
            key = "errors"
        if key == "warning":
            key = "warnings"
        summary[key] = int(num)
    return summary

def extract_warning_lines(text: str):
    lines = text.splitlines()
    warning_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        if not stripped:
            continue

        # Typical pytest warning summary line:
        # path/to/file.py:123: CategoryName: message
        if re.match(r"^.+?:\d+:\s+[\w.]+Warning:", stripped):
            warning_lines.append({
                "line_index": i,
                "line": stripped,
                "context": "\n".join(lines[max(0, i-1): min(len(lines), i+3)]),
            })
            continue

        # Other warning-like lines.
        if "Warning:" in stripped or "warnings.warn" in stripped:
            warning_lines.append({
                "line_index": i,
                "line": stripped,
                "context": "\n".join(lines[max(0, i-1): min(len(lines), i+3)]),
            })

    return warning_lines

def classify_warning(line: str):
    m = re.match(r"^(?P<path>.+?):(?P<line_no>\d+):\s+(?P<category>[\w.]+Warning):\s+(?P<message>.*)$", line)

    if m:
        path = m.group("path")
        line_no = int(m.group("line_no"))
        category = m.group("category")
        message = m.group("message")
    else:
        path = None
        line_no = None
        category_match = re.search(r"([\w.]+Warning):", line)
        category = category_match.group(1) if category_match else "UnknownWarning"
        message = line

    low = line.lower()

    if "datetime.utcnow" in low or "utcnow" in low:
        family = "datetime_utcnow_deprecation"
        fix_strategy = "datetime.utcnow() yerine timezone-aware datetime.now(timezone.utc) kullanılmalı."
    elif "sqlalchemy" in low or "legacyapiwarning" in low or "query.get" in low:
        family = "sqlalchemy_legacy_api"
        fix_strategy = "SQLAlchemy legacy API çağrısı modern Session.get / select tabanlı kullanıma taşınmalı."
    elif "deprecationwarning" in low:
        family = "generic_deprecation"
        fix_strategy = "Uyarı mesajındaki deprecated kullanım modern karşılığına taşınmalı."
    elif "pytest" in low:
        family = "pytest_warning"
        fix_strategy = "Test konfigürasyonu veya fixture kullanımındaki pytest uyarısı hedeflenmeli."
    elif "resourcewarning" in low:
        family = "resource_warning"
        fix_strategy = "Açık dosya/socket/session kapatma akışı netleştirilmeli."
    elif "pendingdeprecationwarning" in low:
        family = "pending_deprecation"
        fix_strategy = "Yaklaşan deprecated kullanım için güvenli modern karşılık planlanmalı."
    else:
        family = "manual_review"
        fix_strategy = "Uyarı türü manuel incelenmeli; doğrudan bastırma yapılmamalı."

    return {
        "path": path,
        "line_no": line_no,
        "category": category,
        "message": message,
        "family": family,
        "fix_strategy": fix_strategy,
        "raw": line,
    }

def main():
    pytest_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "pytest",
        "tests",
        "--ignore=tests/_archive_a5_obsolete",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
    ])

    RAW_TXT.parent.mkdir(parents=True, exist_ok=True)
    RAW_TXT.write_text(pytest_result["combined"], encoding="utf-8")

    pytest_summary = parse_pytest_summary(pytest_result["combined"])
    warning_lines = extract_warning_lines(pytest_result["combined"])
    warning_items = [classify_warning(row["line"]) | {"context": row["context"]} for row in warning_lines]

    by_family = Counter(item["family"] for item in warning_items)
    by_category = Counter(item["category"] for item in warning_items)
    by_path = Counter(item["path"] or "unknown" for item in warning_items)

    grouped = defaultdict(list)
    for item in warning_items:
        grouped[item["family"]].append(item)

    ok = (
        pytest_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
        and pytest_summary.get("warnings", 0) > 0
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A11A_WARNING_AUDIT",
        "mode": "audit_only",
        "ok": ok,
        "decision": "A11A_WARNING_AUDIT_GREEN" if ok else "A11A_WARNING_AUDIT_NOT_GREEN",
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "raw_pytest_output": str(RAW_TXT),
        "extracted_warning_line_count": len(warning_lines),
        "warning_item_count": len(warning_items),
        "by_family": dict(by_family),
        "by_category": dict(by_category),
        "by_path_top_30": dict(by_path.most_common(30)),
        "grouped": dict(grouped),
        "next_action": "A11B: En büyük warning ailesi seçilip güvenli düzeltme uygulanacak. Kod değiştirmeden önce uyarı ailesi netleşti.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A11A Warning Audit",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Karar: {result['decision']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        f"- Extracted warning line count: {result['extracted_warning_line_count']}",
        f"- Warning item count: {result['warning_item_count']}",
        "",
        "## Pytest Özeti",
        "",
        "```json",
        json.dumps(result["pytest_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Warning Family Dağılımı",
        "",
        "```json",
        json.dumps(result["by_family"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Warning Category Dağılımı",
        "",
        "```json",
        json.dumps(result["by_category"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## En Çok Warning Üreten Dosyalar",
        "",
        "```json",
        json.dumps(result["by_path_top_30"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Gruplanmış Warning Detayı",
        "",
        "```json",
        json.dumps(result["grouped"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A11A_REPORT_JSON:", OUT_JSON)
    print("A11A_REPORT_MD:", OUT_MD)
    print("A11A_RAW_PYTEST_OUTPUT:", RAW_TXT)
    print("A11A_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A11A_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A11A_EXTRACTED_WARNING_LINE_COUNT:", result["extracted_warning_line_count"])
    print("A11A_WARNING_ITEM_COUNT:", result["warning_item_count"])
    print("A11A_BY_FAMILY:", json.dumps(result["by_family"], ensure_ascii=False))
    print("A11A_BY_CATEGORY:", json.dumps(result["by_category"], ensure_ascii=False))
    print("A11A_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
