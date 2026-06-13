from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter
import json
import os
import re
import subprocess

ROOT = Path(".").resolve()
QUALITY = ROOT / "reports" / "quality"

A12C_JSON = QUALITY / "BYS360_A12C_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP.json"

OUT_JSON = QUALITY / "BYS360_A12D_UI_TECHNICAL_LANGUAGE_FULL_SCOPE_GATE.json"
OUT_MD = QUALITY / "BYS360_A12D_UI_TECHNICAL_LANGUAGE_FULL_SCOPE_GATE.md"

SCAN_ROOTS = [
    Path("app/templates"),
    Path("app/static/js"),
    Path("app/static/css"),
    Path("app/blueprints"),
    Path("app/routes"),
    Path("app/views"),
]

INCLUDE_SUFFIXES = {".html", ".jinja", ".jinja2", ".js", ".py"}

EXCLUDE_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "reports",
    "logs",
    "tests",
    "migrations",
    "scripts",
    ".venv",
}

TECH_TERMS = [
    "Traceback",
    "Stack trace",
    "Internal Server Error",
    "SQLAlchemy",
    "Alembic",
    "Exception",
    "Hotfix",
    "hotfix",
    "rollback",
    "Rollback",
    "endpoint",
    "blueprint",
    "csrf token",
    "CSRF token",
    "database error",
    "Database error",
    "backend",
    "env",
    "migration",
    "Migration",
    "SQL hotfix",
    "unauthorized_scope",
    "workflow state",
    "phase sync",
]

PHASE_TERMS = [
    "A10",
    "A11",
    "A12",
    "Phase",
    "phase",
    "Faz",
]

KNOWN_CLEANED_PHRASES = [
    "Hotfix ve rollback kararı yazılı kayıtla yönetilir.",
    "SQL hotfix dosyası",
    "Son hotfix kayıtları",
    "Henüz hotfix kaydı bulunmuyor.",
    "Hotfix kaydı",
    "Hotfix kaydet",
    "route ve backend yetki kontrolleri",
    "route yogunlugu",
    "route erişim kontrolünü",
    "migration görünürlüğü",
    "env sertleştirmesi",
]

FALSE_POSITIVE_HINTS = [
    "devamsızlık",
    "devamsizlik",
    "device-width",
    "max-device-width",
    "development",
    "gelişim",
    "gelisim",
    "routeForCurrentPage",
    "fa-route",
    "routes:",
    "ROUTES",
    "csrfToken",
]


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
    except Exception as exc:
        return {"_read_error": str(exc)}


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
        "combined": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-20000:],
    }


def parse_pytest_summary(text: str) -> dict:
    summary = {}
    pattern = r"(\d+)\s+(failed|passed|error|errors|skipped|deselected|warning|warnings)\b"
    for num, key in re.findall(pattern, text or "", flags=re.IGNORECASE):
        key = key.lower()
        if key == "error":
            key = "errors"
        if key == "warning":
            key = "warnings"
        summary[key] = int(num)

    for key in ["failed", "passed", "errors", "skipped", "deselected", "warnings"]:
        summary.setdefault(key, 0)

    return summary


def should_scan(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix.lower() not in INCLUDE_SUFFIXES:
        return False
    if set(path.parts) & EXCLUDE_PARTS:
        return False
    return True


def is_false_positive(line: str) -> bool:
    low = line.lower()
    return any(x.lower() in low for x in FALSE_POSITIVE_HINTS)


def is_probably_visible(path: Path, line: str) -> bool:
    s = line.strip()
    suffix = path.suffix.lower()

    if not s:
        return False

    if s.startswith(("#", "//", "/*", "*", "{#", "<!--")):
        return False

    if suffix in {".html", ".jinja", ".jinja2"}:
        if re.search(r">\s*[^<>{%]+", s):
            return True
        if any(k in s for k in [
            "title=", "aria-label=", "placeholder=", "data-title=",
            "data-label=", "data-message=", "alt="
        ]):
            return True
        return False

    if suffix == ".js":
        if any(k in s for k in [
            "innerText", "textContent", "alert(", "toast", "notify",
            "message:", "title:", "label:", "description:", "placeholder:"
        ]):
            return True
        return False

    if suffix == ".py":
        if any(k in s for k in [
            "flash(", "render_template(", "jsonify(",
            '"message"', "'message'", '"title"', "'title'",
            '"label"', "'label'", '"description"', "'description'"
        ]):
            return True
        return False

    return False


def term_exists(term: str, line: str) -> bool:
    if term in {"Faz", "Phase", "phase"}:
        return re.search(rf"\b{re.escape(term)}\b", line) is not None
    return term in line


def scan_visible_candidates() -> list[dict]:
    findings = []

    for root in SCAN_ROOTS:
        if not root.exists():
            continue

        for path in sorted(root.rglob("*")):
            if not should_scan(path):
                continue

            text = path.read_text(encoding="utf-8-sig", errors="ignore")
            for line_no, line in enumerate(text.splitlines(), start=1):
                if not is_probably_visible(path, line):
                    continue
                if is_false_positive(line):
                    continue

                for term in TECH_TERMS + PHASE_TERMS:
                    if term_exists(term, line):
                        findings.append({
                            "path": str(path).replace("\\", "/"),
                            "line_no": line_no,
                            "term": term,
                            "line": line.strip()[:700],
                        })

    return findings


def scan_known_cleaned_phrases() -> list[dict]:
    remaining = []

    for root in SCAN_ROOTS:
        if not root.exists():
            continue

        for path in sorted(root.rglob("*")):
            if not should_scan(path):
                continue

            text = path.read_text(encoding="utf-8-sig", errors="ignore")
            for phrase in KNOWN_CLEANED_PHRASES:
                if phrase in text:
                    remaining.append({
                        "path": str(path).replace("\\", "/"),
                        "phrase": phrase,
                    })

    return remaining


def count_scanned_files() -> int:
    total = 0
    for root in SCAN_ROOTS:
        if root.exists():
            total += sum(1 for p in root.rglob("*") if should_scan(p))
    return total


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)

    a12c = read_json(A12C_JSON)
    visible_candidates = scan_visible_candidates()
    remaining_known = scan_known_cleaned_phrases()

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

    tests_ok = (
        compile_result["returncode"] == 0
        and pytest_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
    )

    by_term = Counter(item["term"] for item in visible_candidates)
    by_path = Counter(item["path"] for item in visible_candidates)

    ok = (
        a12c.get("ok") is True
        and tests_ok
        and len(remaining_known) == 0
        and len(visible_candidates) == 0
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A12D_UI_TECHNICAL_LANGUAGE_FULL_SCOPE_GATE",
        "mode": "audit_only_no_code_change",
        "ok": ok,
        "decision": "A12D_FULL_SCOPE_GATE_GREEN" if ok else "A12D_REVIEW_OR_A12E_CLEANUP_REQUIRED",
        "source_a12c_ok": a12c.get("ok"),
        "scanned_file_count": count_scanned_files(),
        "visible_candidate_count": len(visible_candidates),
        "remaining_known_cleaned_phrase_count": len(remaining_known),
        "remaining_known_cleaned_phrases": remaining_known,
        "candidate_by_term": dict(by_term),
        "candidate_by_path_top_80": dict(by_path.most_common(80)),
        "visible_candidates": visible_candidates[:1000],
        "compileall_returncode": compile_result["returncode"],
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "next_action": "A12E güvenli temizlik gerekir." if visible_candidates else "A12E final evidence paketine geçilebilir.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 A12D UI Teknik Dil Tam Kapsam Gate",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Source A12C OK: {result['source_a12c_ok']}",
        f"- Taranan dosya sayısı: {result['scanned_file_count']}",
        f"- Visible candidate count: {result['visible_candidate_count']}",
        f"- Remaining known cleaned phrase count: {result['remaining_known_cleaned_phrase_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        "",
        "## Pytest Summary",
        "",
        "```json",
        json.dumps(pytest_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Candidate by Term",
        "",
        "```json",
        json.dumps(result["candidate_by_term"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Candidate by Path",
        "",
        "```json",
        json.dumps(result["candidate_by_path_top_80"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Remaining Known Cleaned Phrases",
        "",
        "```json",
        json.dumps(remaining_known, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Visible Candidates",
        "",
        "```json",
        json.dumps(result["visible_candidates"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("A12D_REPORT_JSON:", OUT_JSON)
    print("A12D_REPORT_MD:", OUT_MD)
    print("A12D_SOURCE_A12C_OK:", result["source_a12c_ok"])
    print("A12D_SCANNED_FILE_COUNT:", result["scanned_file_count"])
    print("A12D_VISIBLE_CANDIDATE_COUNT:", result["visible_candidate_count"])
    print("A12D_REMAINING_KNOWN_CLEANED_PHRASE_COUNT:", result["remaining_known_cleaned_phrase_count"])
    print("A12D_BY_TERM:", json.dumps(result["candidate_by_term"], ensure_ascii=False))
    print("A12D_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A12D_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A12D_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A12D_OK:", result["ok"])

    return 0 if tests_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
