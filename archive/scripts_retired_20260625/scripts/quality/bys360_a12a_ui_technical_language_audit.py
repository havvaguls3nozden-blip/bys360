from pathlib import Path
from datetime import datetime
import json
import subprocess
import os
import re
from collections import Counter, defaultdict

ROOT = Path(".").resolve()

OUT_JSON = Path("reports/quality/BYS360_A12A_UI_TECHNICAL_LANGUAGE_AUDIT.json")
OUT_MD = Path("reports/quality/BYS360_A12A_UI_TECHNICAL_LANGUAGE_AUDIT.md")

SCAN_ROOTS = [
    Path("app/templates"),
    Path("app/static"),
    Path("app/blueprints"),
    Path("app/routes"),
    Path("app/views"),
]

INCLUDE_SUFFIXES = {".html", ".jinja", ".jinja2", ".js", ".css", ".py"}

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

TECHNICAL_TERMS = {
    "hard_ui": [
        "Traceback",
        "Stack trace",
        "Internal Server Error",
        "SQLAlchemy",
        "Alembic",
        "migration",
        "Exception",
        "Debug",
        "debug",
        "hotfix",
        "Hotfix",
        "repair",
        "Repair",
        "dev",
        "DEV",
        "endpoint",
        "blueprint",
        "route",
        "csrf token",
        "CSRF token",
        "database error",
        "Database error",
    ],
    "project_phase_terms": [
        "faz",
        "Faz",
        "phase",
        "Phase",
        "A10",
        "A11",
        "A12",
        "P1",
        "P2",
        "P3",
        "V1",
        "V2",
    ],
    "developer_ui_terms": [
        "TODO",
        "FIXME",
        "console.log",
        "localhost",
        "127.0.0.1",
        "mock",
        "dummy",
        "placeholder",
    ],
}

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

def should_scan(path: Path):
    if not path.is_file():
        return False
    if path.suffix.lower() not in INCLUDE_SUFFIXES:
        return False
    parts = set(path.parts)
    if parts & EXCLUDE_PARTS:
        return False
    return True

def classify_file(path: Path):
    p = str(path).replace("\\", "/")
    if "/templates/" in p or p.startswith("app/templates/"):
        return "template_user_visible"
    if "/static/" in p or p.startswith("app/static/"):
        if path.suffix.lower() in {".js", ".css"}:
            return "static_user_visible_asset"
    if path.suffix.lower() == ".py":
        return "python_possible_user_message"
    return "other_review"

def find_hits(path: Path):
    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    lines = text.splitlines()
    findings = []

    for line_no, line in enumerate(lines, start=1):
        for family, terms in TECHNICAL_TERMS.items():
            for term in terms:
                if term in line:
                    stripped = line.strip()
                    if not stripped:
                        continue

                    findings.append({
                        "path": str(path).replace("\\", "/"),
                        "line_no": line_no,
                        "family": family,
                        "term": term,
                        "file_class": classify_file(path),
                        "line": stripped[:500],
                    })

    return findings

def main():
    all_files = []
    for root in SCAN_ROOTS:
        if root.exists():
            all_files.extend([p for p in root.rglob("*") if should_scan(p)])

    findings = []
    for path in sorted(all_files):
        findings.extend(find_hits(path))

    by_family = Counter(item["family"] for item in findings)
    by_file_class = Counter(item["file_class"] for item in findings)
    by_path = Counter(item["path"] for item in findings)

    high_risk = [
        item for item in findings
        if item["family"] == "hard_ui"
        and item["file_class"] in {"template_user_visible", "static_user_visible_asset", "python_possible_user_message"}
    ]

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
        compile_result["returncode"] == 0
        and pytest_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A12A_UI_TECHNICAL_LANGUAGE_AUDIT",
        "mode": "audit_only_no_code_change",
        "ok": ok,
        "decision": "A12A_AUDIT_COMPLETED" if ok else "A12A_AUDIT_NOT_GREEN",
        "scanned_file_count": len(all_files),
        "finding_count": len(findings),
        "high_risk_user_visible_count": len(high_risk),
        "by_family": dict(by_family),
        "by_file_class": dict(by_file_class),
        "by_path_top_50": dict(by_path.most_common(50)),
        "high_risk_user_visible": high_risk[:300],
        "findings": findings[:1000],
        "compileall_returncode": compile_result["returncode"],
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "next_action": "A12B: high_risk_user_visible listesindeki gerçek kullanıcıya görünen teknik ifadeler güvenli metinlerle değiştirilecek.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A12A UI Teknik Dil Audit",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Karar: {result['decision']}",
        f"- Taranan dosya sayısı: {result['scanned_file_count']}",
        f"- Finding count: {result['finding_count']}",
        f"- High risk user visible count: {result['high_risk_user_visible_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        "",
        "## Pytest Summary",
        "",
        "```json",
        json.dumps(pytest_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Family Dağılımı",
        "",
        "```json",
        json.dumps(result["by_family"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## File Class Dağılımı",
        "",
        "```json",
        json.dumps(result["by_file_class"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## En Çok Bulgu Olan Dosyalar",
        "",
        "```json",
        json.dumps(result["by_path_top_50"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## High Risk User Visible Bulgular",
        "",
        "```json",
        json.dumps(result["high_risk_user_visible"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A12A_REPORT_JSON:", OUT_JSON)
    print("A12A_REPORT_MD:", OUT_MD)
    print("A12A_SCANNED_FILE_COUNT:", result["scanned_file_count"])
    print("A12A_FINDING_COUNT:", result["finding_count"])
    print("A12A_HIGH_RISK_USER_VISIBLE_COUNT:", result["high_risk_user_visible_count"])
    print("A12A_BY_FAMILY:", json.dumps(result["by_family"], ensure_ascii=False))
    print("A12A_BY_FILE_CLASS:", json.dumps(result["by_file_class"], ensure_ascii=False))
    print("A12A_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A12A_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A12A_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A12A_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
