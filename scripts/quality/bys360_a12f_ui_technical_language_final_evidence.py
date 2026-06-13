from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter
import hashlib
import json
import os
import re
import subprocess
import zipfile

ROOT = Path(".").resolve()
QUALITY = ROOT / "reports" / "quality"
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

A11C_JSON = QUALITY / "BYS360_A11C_WARNING_ZERO_FINAL_EVIDENCE.json"
A12C_JSON = QUALITY / "BYS360_A12C_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP.json"
A12D_JSON = QUALITY / "BYS360_A12D_UI_TECHNICAL_LANGUAGE_FULL_SCOPE_GATE.json"
A12E_JSON = QUALITY / "BYS360_A12E_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP.json"

OUT_JSON = QUALITY / "BYS360_A12F_UI_TECHNICAL_LANGUAGE_FINAL_EVIDENCE.json"
OUT_MD = QUALITY / "BYS360_A12F_UI_TECHNICAL_LANGUAGE_FINAL_EVIDENCE.md"
OUT_ZIP = RELEASES / f"BYS360_A12F_UI_TECHNICAL_LANGUAGE_FINAL_EVIDENCE_{STAMP}.zip"

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
    "migration",
    "Migration",
    "SQL hotfix",
    "unauthorized_scope",
    "workflow state",
    "phase sync",
]

PHASE_TERMS = ["A10", "A11", "A12", "Phase", "phase", "Faz"]

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

VISIBLE_ATTRS = [
    "title",
    "aria-label",
    "placeholder",
    "data-title",
    "data-label",
    "data-message",
    "alt",
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
    "fa-envelope",
    "envelope",
    "environment:",
]


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
    except Exception as exc:
        return {"_read_error": str(exc), "_path": str(path)}


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


def mask_jinja(text: str) -> str:
    return re.sub(r"({{.*?}}|{%.*?%}|{#.*?#})", "", text)


def is_false_positive(text: str) -> bool:
    low = text.lower()
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
        if any(f"{attr}=" in s for attr in VISIBLE_ATTRS):
            return True
        return False

    if suffix == ".js":
        return any(k in s for k in [
            "innerText", "textContent", "alert(", "toast", "notify",
            "message:", "title:", "label:", "description:", "placeholder:",
            "setAttribute('aria-label'", 'setAttribute("aria-label"',
        ])

    if suffix == ".py":
        return any(k in s for k in [
            "flash(", "render_template(", "jsonify(",
            '"message"', "'message'", '"title"', "'title'",
            '"label"', "'label'", '"description"', "'description'",
        ])

    return False


def visible_segments_from_html(line: str) -> list[str]:
    masked = mask_jinja(line)
    segments = []

    for match in re.finditer(r">([^<]+)<", masked):
        value = match.group(1).strip()
        if value:
            segments.append(value)

    for attr in VISIBLE_ATTRS:
        pattern = rf"{re.escape(attr)}\s*=\s*([\"'])(.*?)\1"
        for match in re.finditer(pattern, masked, flags=re.IGNORECASE):
            value = match.group(2).strip()
            if value:
                segments.append(value)

    return segments


def visible_segments_from_code(line: str) -> list[str]:
    masked = mask_jinja(line)
    segments = []
    for match in re.finditer(r"(['\"])(.*?)(?<!\\)\1", masked):
        value = match.group(2).strip()
        if value:
            segments.append(value)
    return segments


def candidate_terms_in_segment(segment: str) -> list[str]:
    if is_false_positive(segment):
        return []

    hits = []

    for term in TECH_TERMS:
        if term in segment:
            hits.append(term)

    for term in PHASE_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", segment):
            hits.append(term)

    return hits


def scan_visible_candidates() -> list[dict]:
    findings = []

    for root in SCAN_ROOTS:
        if not root.exists():
            continue

        for path in sorted(root.rglob("*")):
            if not should_scan(path):
                continue

            suffix = path.suffix.lower()
            text = path.read_text(encoding="utf-8-sig", errors="ignore")

            for line_no, line in enumerate(text.splitlines(), start=1):
                if not is_probably_visible(path, line):
                    continue

                if suffix in {".html", ".jinja", ".jinja2"}:
                    segments = visible_segments_from_html(line)
                else:
                    segments = visible_segments_from_code(line)

                for segment in segments:
                    for term in candidate_terms_in_segment(segment):
                        findings.append({
                            "path": str(path).replace("\\", "/"),
                            "line_no": line_no,
                            "term": term,
                            "segment": segment[:700],
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


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return path.name


def unique_existing(paths: list[Path]) -> list[Path]:
    seen = set()
    result = []

    for path in paths:
        if not path.exists() or not path.is_file():
            continue

        key = str(path.resolve()).lower()
        if key in seen:
            continue

        seen.add(key)
        result.append(path)

    return result


def collect_evidence_files(a12e: dict) -> list[Path]:
    files = []

    for pattern in [
        "BYS360_A11C*",
        "BYS360_A12C*",
        "BYS360_A12D*",
        "BYS360_A12E*",
        "BYS360_A12F*",
    ]:
        files.extend(sorted(QUALITY.glob(pattern)))

    for script_name in [
        "bys360_a11c_warning_zero_final_evidence.py",
        "bys360_a12c_ui_technical_language_safe_cleanup.py",
        "bys360_a12d_ui_technical_language_full_scope_gate.py",
        "bys360_a12e_ui_technical_language_safe_cleanup.py",
        "bys360_a12f_ui_technical_language_final_evidence.py",
    ]:
        files.append(ROOT / "scripts" / "quality" / script_name)

    for item in a12e.get("operations", []):
        raw = item.get("path")
        if raw:
            files.append(ROOT / raw)

    return unique_existing(files)


def write_reports(result: dict) -> None:
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A12F UI Teknik Dil Final Evidence",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Source A11C OK: {result['source_a11c_ok']}",
        f"- Source A12C OK: {result['source_a12c_ok']}",
        f"- Source A12E OK: {result['source_a12e_ok']}",
        f"- A12E post visible candidate count: {result['source_a12e_post_visible_candidate_count']}",
        f"- Final visible candidate count: {result['final_visible_candidate_count']}",
        f"- Final known old phrase count: {result['final_known_old_phrase_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        f"- Duplicate ZIP entry count: {result['duplicate_zip_entry_count']}",
        "",
        "## Pytest Summary",
        "",
        "```json",
        json.dumps(result["pytest_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Final Candidate by Term",
        "",
        "```json",
        json.dumps(result["final_candidate_by_term"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Final Visible Candidates",
        "",
        "```json",
        json.dumps(result["final_visible_candidates"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Evidence ZIP",
        "",
        f"- ZIP: `{result['evidence_zip']}`",
        f"- SHA256: `{result['evidence_zip_sha256']}`",
        f"- Evidence file count: {result['evidence_file_count']}",
        f"- ZIP entry count: {result['zip_entry_count']}",
        "",
        "## Sonraki Faz",
        "",
        result["next_phase"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)
    RELEASES.mkdir(parents=True, exist_ok=True)

    a11c = read_json(A11C_JSON)
    a12c = read_json(A12C_JSON)
    a12d = read_json(A12D_JSON)
    a12e = read_json(A12E_JSON)

    final_candidates = scan_visible_candidates()
    final_known_old_phrases = scan_known_cleaned_phrases()

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
        and pytest_summary.get("warnings", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
    )

    by_term = Counter(item["term"] for item in final_candidates)

    ok = (
        a11c.get("ok") is True
        and a12c.get("ok") is True
        and a12e.get("ok") is True
        and a12e.get("post_visible_candidate_count") == 0
        and a12e.get("remaining_known_cleaned_phrase_count") == 0
        and len(final_candidates) == 0
        and len(final_known_old_phrases) == 0
        and tests_ok
    )

    preliminary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A12F_UI_TECHNICAL_LANGUAGE_FINAL_EVIDENCE",
        "ok": ok,
        "decision": "A12F_FINAL_EVIDENCE_GREEN" if ok else "A12F_REVIEW_REQUIRED",
        "source_a11c_ok": a11c.get("ok"),
        "source_a12c_ok": a12c.get("ok"),
        "source_a12d_visible_candidate_count": a12d.get("visible_candidate_count"),
        "source_a12e_ok": a12e.get("ok"),
        "source_a12e_target_file_count": a12e.get("target_file_count"),
        "source_a12e_total_changed_line_count": a12e.get("total_changed_line_count"),
        "source_a12e_post_visible_candidate_count": a12e.get("post_visible_candidate_count"),
        "source_a12e_remaining_known_cleaned_phrase_count": a12e.get("remaining_known_cleaned_phrase_count"),
        "final_visible_candidate_count": len(final_candidates),
        "final_known_old_phrase_count": len(final_known_old_phrases),
        "final_candidate_by_term": dict(by_term),
        "final_visible_candidates": final_candidates[:1000],
        "final_known_old_phrases": final_known_old_phrases,
        "compileall_returncode": compile_result["returncode"],
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "evidence_zip": str(OUT_ZIP),
        "evidence_zip_sha256": "",
        "evidence_file_count": 0,
        "zip_entry_count": 0,
        "duplicate_zip_entry_count": 0,
        "duplicate_zip_entries": [],
        "next_phase": "A13_UI_DESIGN_SYSTEM_AND_COMPONENT_STANDARDIZATION" if ok else "A12_REVIEW_REQUIRED",
    }

    write_reports(preliminary)

    evidence_files = collect_evidence_files(a12e)

    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in evidence_files:
            zf.write(path, rel(path))

    with zipfile.ZipFile(OUT_ZIP, "r") as zf:
        names = zf.namelist()

    duplicates = sorted([name for name, count in Counter(names).items() if count > 1])
    sha = hashlib.sha256(OUT_ZIP.read_bytes()).hexdigest()

    final = {
        **preliminary,
        "evidence_zip_sha256": sha,
        "evidence_file_count": len(evidence_files),
        "zip_entry_count": len(names),
        "duplicate_zip_entry_count": len(duplicates),
        "duplicate_zip_entries": duplicates,
    }

    final["ok"] = bool(ok and not duplicates)
    final["decision"] = "A12F_FINAL_EVIDENCE_GREEN" if final["ok"] else "A12F_REVIEW_REQUIRED"
    final["next_phase"] = "A13_UI_DESIGN_SYSTEM_AND_COMPONENT_STANDARDIZATION" if final["ok"] else "A12_REVIEW_REQUIRED"

    write_reports(final)

    print("A12F_REPORT_JSON:", OUT_JSON)
    print("A12F_REPORT_MD:", OUT_MD)
    print("A12F_EVIDENCE_ZIP:", OUT_ZIP)
    print("A12F_EVIDENCE_ZIP_SHA256:", sha)
    print("A12F_SOURCE_A11C_OK:", final["source_a11c_ok"])
    print("A12F_SOURCE_A12C_OK:", final["source_a12c_ok"])
    print("A12F_SOURCE_A12E_OK:", final["source_a12e_ok"])
    print("A12F_SOURCE_A12E_POST_VISIBLE_CANDIDATE_COUNT:", final["source_a12e_post_visible_candidate_count"])
    print("A12F_FINAL_VISIBLE_CANDIDATE_COUNT:", final["final_visible_candidate_count"])
    print("A12F_FINAL_KNOWN_OLD_PHRASE_COUNT:", final["final_known_old_phrase_count"])
    print("A12F_COMPILEALL_RETURN_CODE:", final["compileall_returncode"])
    print("A12F_PYTEST_RETURN_CODE:", final["pytest_returncode"])
    print("A12F_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A12F_DUPLICATE_ZIP_ENTRY_COUNT:", final["duplicate_zip_entry_count"])
    print("A12F_OK:", final["ok"])

    return 0 if final["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
