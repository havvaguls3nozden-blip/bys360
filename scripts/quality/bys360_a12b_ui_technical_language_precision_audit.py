from pathlib import Path
from datetime import datetime
import json
import subprocess
import os
import re
from collections import Counter

ROOT = Path(".").resolve()

A12A_JSON = Path("reports/quality/BYS360_A12A_UI_TECHNICAL_LANGUAGE_AUDIT.json")

OUT_JSON = Path("reports/quality/BYS360_A12B_UI_TECHNICAL_LANGUAGE_PRECISION_AUDIT.json")
OUT_MD = Path("reports/quality/BYS360_A12B_UI_TECHNICAL_LANGUAGE_PRECISION_AUDIT.md")

FALSE_POSITIVE_SUBSTRINGS = [
    "devamsızlık",
    "devamsizlik",
    "device-width",
    "max-device-width",
    "development",
    "gelisim",
    "gelişim",
]

VISIBLE_KEYS = [
    "title",
    "text",
    "message",
    "label",
    "placeholder",
    "action",
    "description",
    "summary",
    "body",
    "help",
    "aria-label",
    "data-title",
    "data-label",
    "data-message",
]

TECHNICAL_WORDS_STRICT = [
    "Traceback",
    "Stack trace",
    "Internal Server Error",
    "SQLAlchemy",
    "Alembic",
    "Exception",
    "hotfix",
    "Hotfix",
    "repair",
    "Repair",
    "endpoint",
    "blueprint",
    "csrf token",
    "CSRF token",
    "database error",
    "Database error",
]

PROJECT_WORDS_STRICT = [
    "A10",
    "A11",
    "A12",
    "P1",
    "P2",
    "P3",
    "Phase",
    "phase",
    "Faz",
    "faz",
]

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
            "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS": "1",
        },
        timeout=timeout,
    )
    return {
        "cmd": " ".join(map(str, cmd)),
        "returncode": proc.returncode,
        "combined": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-12000:],
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

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))

def has_strict_technical_term(line: str):
    for word in TECHNICAL_WORDS_STRICT + PROJECT_WORDS_STRICT:
        if word in line:
            return True
    return False

def is_false_positive_substring(term: str, line: str):
    low = line.lower()

    if term.lower() == "dev":
        if any(x in low for x in FALSE_POSITIVE_SUBSTRINGS):
            return True

        # "dev" sadece bağımsız kelime değilse yanlış pozitif say.
        if not re.search(r"(?<![A-Za-zÇĞİÖŞÜçğıöşü])dev(?![A-Za-zÇĞİÖŞÜçğıöşü])", low):
            return True

    if term.lower() == "route":
        # routeForCurrentPage gibi kod isimleri
        if re.search(r"\broute[A-Z_]", line) or "function route" in line:
            return True

    return False

def is_css_code_line(line: str):
    s = line.strip()
    return (
        s.startswith(".")
        or s.startswith("#")
        or s.startswith("@media")
        or s.startswith("@keyframes")
        or "{" in s
        or "}" in s
        or ":" in s and ";" in s
        or s.startswith("/*")
        or s.endswith("*/")
    )

def is_js_code_identifier_line(line: str):
    s = line.strip()

    code_starts = (
        "function ",
        "var ",
        "let ",
        "const ",
        "return ",
        "if ",
        "for ",
        "while ",
        "switch ",
        "case ",
        "//",
        "/*",
        "*",
    )

    if s.startswith(code_starts):
        return True

    if re.search(r"\bfunction\s+\w+\(", s):
        return True

    if re.search(r"\b[A-Za-z_$][\w$]*\s*[:=]\s*function\b", s):
        return True

    if re.search(r"\b[A-Za-z_$][\w$]*\s*\(", s) and not any(k in s for k in VISIBLE_KEYS):
        return True

    return False

def html_visible_text_candidate(line: str):
    s = line.strip()

    if not s:
        return False

    if s.startswith("{#") or s.startswith("<!--"):
        return False

    if "<script" in s or "<style" in s:
        return False

    if "class=" in s and not re.search(r">\s*[^<>{%]+", s):
        return False

    if re.search(r">\s*[^<>{%]+", s):
        return True

    for key in VISIBLE_KEYS:
        if f"{key}=" in s:
            return True

    return False

def js_visible_string_candidate(line: str):
    s = line.strip()

    # JS obje alanlarında kullanıcıya görünen metin olma ihtimali yüksek alanlar
    if re.search(r"\b(title|text|message|label|placeholder|action|description|summary|help)\s*:", s):
        return True

    if any(x in s for x in ["innerText", "textContent", "setAttribute('aria-label'", 'setAttribute("aria-label"', "alert(", "toast", "notify"]):
        return True

    return False

def classify_finding(item):
    path = item.get("path", "")
    line = item.get("line", "")
    term = item.get("term", "")
    family = item.get("family", "")
    suffix = Path(path).suffix.lower()

    if is_false_positive_substring(term, line):
        return "false_positive_substring"

    if suffix == ".css":
        return "false_positive_css_not_visible"

    if suffix in {".js"}:
        if js_visible_string_candidate(line) and has_strict_technical_term(line):
            return "real_user_visible_candidate"
        if is_js_code_identifier_line(line):
            return "false_positive_js_code_identifier"
        if js_visible_string_candidate(line):
            return "review_user_visible_string"
        return "false_positive_js_code_or_regex"

    if suffix in {".html", ".jinja", ".jinja2"}:
        if html_visible_text_candidate(line) and has_strict_technical_term(line):
            return "real_user_visible_candidate"
        if html_visible_text_candidate(line):
            return "review_user_visible_text"
        return "false_positive_template_code_or_attribute"

    if suffix == ".py":
        if any(k in line for k in VISIBLE_KEYS) and has_strict_technical_term(line):
            return "real_user_visible_candidate"
        return "review_python_possible_message"

    return "manual_review"

def main():
    if not A12A_JSON.exists():
        raise SystemExit("A12A JSON bulunamadı. Önce A12A çalışmalı.")

    a12a = read_json(A12A_JSON)

    source_items = a12a.get("high_risk_user_visible", [])
    if not source_items:
        source_items = a12a.get("findings", [])

    classified = []
    for item in source_items:
        decision = classify_finding(item)
        row = dict(item)
        row["a12b_decision"] = decision
        classified.append(row)

    by_decision = Counter(row["a12b_decision"] for row in classified)
    by_path_real = Counter(row["path"] for row in classified if row["a12b_decision"] == "real_user_visible_candidate")
    by_path_review = Counter(row["path"] for row in classified if row["a12b_decision"].startswith("review"))

    real_candidates = [row for row in classified if row["a12b_decision"] == "real_user_visible_candidate"]
    review_candidates = [row for row in classified if row["a12b_decision"].startswith("review")]
    false_positive_count = sum(1 for row in classified if row["a12b_decision"].startswith("false_positive"))

    compile_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
        "migrations",
    ])

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

    pytest_summary = parse_pytest_summary(pytest_result["combined"])

    ok = (
        a12a.get("ok") is True
        and compile_result["returncode"] == 0
        and pytest_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A12B_UI_TECHNICAL_LANGUAGE_PRECISION_AUDIT",
        "mode": "precision_audit_only_no_code_change",
        "ok": ok,
        "decision": "A12B_PRECISION_AUDIT_COMPLETED" if ok else "A12B_PRECISION_AUDIT_NOT_GREEN",
        "source_a12a_ok": a12a.get("ok"),
        "source_high_risk_count": len(source_items),
        "classified_count": len(classified),
        "false_positive_count": false_positive_count,
        "real_user_visible_candidate_count": len(real_candidates),
        "review_candidate_count": len(review_candidates),
        "by_decision": dict(by_decision),
        "real_candidates_by_path": dict(by_path_real.most_common(50)),
        "review_candidates_by_path": dict(by_path_review.most_common(50)),
        "real_user_visible_candidates": real_candidates[:300],
        "review_candidates": review_candidates[:300],
        "classified_sample": classified[:500],
        "compileall_returncode": compile_result["returncode"],
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "next_action": "A12C: yalnızca real_user_visible_candidate ve gerekirse review adayları üzerinde güvenli metin temizliği yapılacak.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A12B UI Teknik Dil Precision Audit",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Karar: {result['decision']}",
        f"- Source high risk count: {result['source_high_risk_count']}",
        f"- Classified count: {result['classified_count']}",
        f"- False positive count: {result['false_positive_count']}",
        f"- Real user visible candidate count: {result['real_user_visible_candidate_count']}",
        f"- Review candidate count: {result['review_candidate_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        "",
        "## Pytest Summary",
        "",
        "```json",
        json.dumps(pytest_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Decision Dağılımı",
        "",
        "```json",
        json.dumps(result["by_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Gerçek Kullanıcı Metni Adayları - Dosya Dağılımı",
        "",
        "```json",
        json.dumps(result["real_candidates_by_path"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Review Adayları - Dosya Dağılımı",
        "",
        "```json",
        json.dumps(result["review_candidates_by_path"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Gerçek Kullanıcı Metni Adayları",
        "",
        "```json",
        json.dumps(result["real_user_visible_candidates"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Review Adayları",
        "",
        "```json",
        json.dumps(result["review_candidates"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A12B_REPORT_JSON:", OUT_JSON)
    print("A12B_REPORT_MD:", OUT_MD)
    print("A12B_SOURCE_HIGH_RISK_COUNT:", result["source_high_risk_count"])
    print("A12B_CLASSIFIED_COUNT:", result["classified_count"])
    print("A12B_FALSE_POSITIVE_COUNT:", result["false_positive_count"])
    print("A12B_REAL_USER_VISIBLE_CANDIDATE_COUNT:", result["real_user_visible_candidate_count"])
    print("A12B_REVIEW_CANDIDATE_COUNT:", result["review_candidate_count"])
    print("A12B_BY_DECISION:", json.dumps(result["by_decision"], ensure_ascii=False))
    print("A12B_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A12B_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A12B_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A12B_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
