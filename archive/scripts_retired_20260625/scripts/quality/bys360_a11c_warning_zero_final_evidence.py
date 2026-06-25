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

A11B2_JSON = QUALITY / "BYS360_A11B2_RESOURCE_WARNING_FIX.json"

OUT_JSON = QUALITY / "BYS360_A11C_WARNING_ZERO_FINAL_EVIDENCE.json"
OUT_MD = QUALITY / "BYS360_A11C_WARNING_ZERO_FINAL_EVIDENCE.md"

RAW_PYTEST = QUALITY / "BYS360_A11C_PYTEST_RAW.txt"
RAW_STRICT_UNRAISABLE = QUALITY / "BYS360_A11C_STRICT_UNRAISABLE_RAW.txt"
RAW_STRICT_RESOURCE = QUALITY / "BYS360_A11C_STRICT_RESOURCE_RAW.txt"
INTERNAL_MANIFEST = QUALITY / "BYS360_A11C_EVIDENCE_INTERNAL_MANIFEST.md"

OUT_ZIP = RELEASES / f"BYS360_A11C_WARNING_ZERO_EVIDENCE_{STAMP}.zip"
TARGET_SOURCE = ROOT / "app" / "bootstrap" / "operational_logging.py"


def run_cmd(cmd, timeout=1800):
    env = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS": "1",
    }

    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="ignore",
            env=env,
            timeout=timeout,
        )
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": proc.returncode,
            "combined": combined,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="ignore")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="ignore")
        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": 124,
            "combined": stdout + "\n" + stderr + "\nTIMEOUT",
        }


def read_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
    except Exception as exc:
        return {"_read_error": str(exc), "_path": str(path)}


def parse_pytest_summary(text: str):
    summary = {}
    pattern = r"(\d+)\s+(failed|passed|error|errors|skipped|deselected|warning|warnings)\b"
    for num, key in re.findall(pattern, text, flags=re.IGNORECASE):
        key = key.lower()
        if key == "error":
            key = "errors"
        if key == "warning":
            key = "warnings"
        summary[key] = int(num)

    for key in ["failed", "passed", "errors", "skipped", "deselected", "warnings"]:
        summary.setdefault(key, 0)

    return summary


def has_warning_summary(text: str):
    low = text.lower()
    if "warnings summary" in low:
        return True
    return bool(re.search(r"\b[1-9]\d*\s+warnings?\b", low))


def extract_warning_lines(text: str, limit=120):
    needles = [
        "warning",
        "resourcewarning",
        "pytestunraisable",
        "unclosed",
        "bys360-app.log",
        "bys360-ops.log",
    ]
    hits = []
    for i, line in enumerate(text.splitlines()):
        low = line.lower()
        if any(n in low for n in needles):
            hits.append({"line_no": i + 1, "line": line})
    return hits[:limit]


def rel(path: Path):
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return path.name


def unique_existing(paths):
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


def collect_evidence_files():
    files = []

    for pattern in [
        "BYS360_A11A*",
        "BYS360_A11B*",
        "BYS360_A11C*",
    ]:
        files.extend(sorted(QUALITY.glob(pattern)))

    files.extend([
        TARGET_SOURCE,
        OUT_JSON,
        OUT_MD,
        RAW_PYTEST,
        RAW_STRICT_UNRAISABLE,
        RAW_STRICT_RESOURCE,
        INTERNAL_MANIFEST,
    ])

    return unique_existing(files)


def write_reports(result, pytest_summary, strict_unraisable_summary, strict_resource_summary, warning_lines):
    OUT_JSON.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# BYS360 A11C Warning Zero Final Evidence",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Source A11B2 OK: {result['source_a11b2_ok']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        f"- Strict unraisable returncode: {result['strict_unraisable_returncode']}",
        f"- Strict resource returncode: {result['strict_resource_returncode']}",
        f"- Warnings after: {result['warnings_after']}",
        f"- Pytest warning text var mı: {result['pytest_has_warning_text']}",
        f"- Duplicate ZIP entry count: {result['duplicate_zip_entry_count']}",
        "",
        "## Pytest Summary",
        "",
        "```json",
        json.dumps(pytest_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Strict Unraisable Summary",
        "",
        "```json",
        json.dumps(strict_unraisable_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Strict Resource Summary",
        "",
        "```json",
        json.dumps(strict_resource_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Warning Lines",
        "",
        "```json",
        json.dumps(warning_lines, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Evidence ZIP",
        "",
        f"- ZIP: `{result['evidence_zip']}`",
        f"- SHA256: `{result['evidence_zip_sha256']}`",
        f"- Evidence file count: {result['evidence_file_count']}",
        f"- ZIP entry count: {result['zip_entry_count']}",
        "",
        "## Canlı Notu",
        "",
        result["live_note"],
        "",
        "## Sonraki Faz",
        "",
        result["next_phase"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    QUALITY.mkdir(parents=True, exist_ok=True)
    RELEASES.mkdir(parents=True, exist_ok=True)

    a11b2 = read_json(A11B2_JSON)

    py = ROOT / ".venv" / "Scripts" / "python.exe"
    pytest_cmd = [
        str(py),
        "-m",
        "pytest",
        "tests",
        "--ignore=tests/_archive_a5_obsolete",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
    ]

    compile_result = run_cmd([
        str(py),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
        "migrations",
    ])

    pytest_result = run_cmd(pytest_cmd)
    strict_unraisable_result = run_cmd(
        pytest_cmd + ["-W", "error::pytest.PytestUnraisableExceptionWarning"]
    )
    strict_resource_result = run_cmd(
        pytest_cmd + ["-W", "error::ResourceWarning"]
    )

    RAW_PYTEST.write_text(pytest_result["combined"], encoding="utf-8")
    RAW_STRICT_UNRAISABLE.write_text(strict_unraisable_result["combined"], encoding="utf-8")
    RAW_STRICT_RESOURCE.write_text(strict_resource_result["combined"], encoding="utf-8")

    pytest_summary = parse_pytest_summary(pytest_result["combined"])
    strict_unraisable_summary = parse_pytest_summary(strict_unraisable_result["combined"])
    strict_resource_summary = parse_pytest_summary(strict_resource_result["combined"])

    warning_lines = extract_warning_lines(pytest_result["combined"])
    strict_unraisable_warning_lines = extract_warning_lines(strict_unraisable_result["combined"])
    strict_resource_warning_lines = extract_warning_lines(strict_resource_result["combined"])

    warnings_after = pytest_summary.get("warnings", 0)
    pytest_has_warning_text = has_warning_summary(pytest_result["combined"])
    strict_unraisable_has_warning_text = has_warning_summary(strict_unraisable_result["combined"])
    strict_resource_has_warning_text = has_warning_summary(strict_resource_result["combined"])

    source_a11b2_ok = a11b2.get("ok") is True

    ok = (
        source_a11b2_ok
        and compile_result["returncode"] == 0
        and pytest_result["returncode"] == 0
        and strict_unraisable_result["returncode"] == 0
        and strict_resource_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
        and strict_unraisable_summary.get("failed", 0) == 0
        and strict_unraisable_summary.get("errors", 0) == 0
        and strict_unraisable_summary.get("passed", 0) >= 700
        and strict_resource_summary.get("failed", 0) == 0
        and strict_resource_summary.get("errors", 0) == 0
        and strict_resource_summary.get("passed", 0) >= 700
        and warnings_after == 0
        and not pytest_has_warning_text
        and not strict_unraisable_has_warning_text
        and not strict_resource_has_warning_text
    )

    INTERNAL_MANIFEST.write_text(
        "\n".join([
            "# BYS360 A11C Warning Zero Evidence Internal Manifest",
            "",
            "Bu paket A11 warning-zero kapanış kanıtlarını içerir.",
            "ZIP SHA256 değeri dış A11C raporunda tutulur.",
            "",
            "## Evidence Rules",
            "",
            "- Normal pytest yeşil olmalı.",
            "- ResourceWarning strict koşusu yeşil olmalı.",
            "- PytestUnraisable strict koşusu yeşil olmalı.",
            "- Warning summary bulunmamalı.",
            "- ZIP içinde duplicate entry olmamalı.",
            "",
        ]),
        encoding="utf-8",
    )

    preliminary_result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A11C_WARNING_ZERO_FINAL_EVIDENCE",
        "ok": ok,
        "decision": "accepted_warning_zero" if ok else "blocked_manual_review",
        "source_a11b2_ok": source_a11b2_ok,
        "source_a11b2_json": str(A11B2_JSON),
        "compileall_returncode": compile_result["returncode"],
        "pytest_returncode": pytest_result["returncode"],
        "strict_unraisable_returncode": strict_unraisable_result["returncode"],
        "strict_resource_returncode": strict_resource_result["returncode"],
        "pytest_summary": pytest_summary,
        "strict_unraisable_summary": strict_unraisable_summary,
        "strict_resource_summary": strict_resource_summary,
        "warnings_after": warnings_after,
        "pytest_has_warning_text": pytest_has_warning_text,
        "strict_unraisable_has_warning_text": strict_unraisable_has_warning_text,
        "strict_resource_has_warning_text": strict_resource_has_warning_text,
        "warning_lines": warning_lines,
        "strict_unraisable_warning_lines": strict_unraisable_warning_lines,
        "strict_resource_warning_lines": strict_resource_warning_lines,
        "raw_files": {
            "pytest": str(RAW_PYTEST),
            "strict_unraisable": str(RAW_STRICT_UNRAISABLE),
            "strict_resource": str(RAW_STRICT_RESOURCE),
        },
        "evidence_zip": str(OUT_ZIP),
        "evidence_zip_sha256": "",
        "evidence_file_count": 0,
        "zip_entry_count": 0,
        "duplicate_zip_entry_count": 0,
        "duplicate_zip_entries": [],
        "next_phase": "A12_UI_TECHNICAL_LANGUAGE_CLEANUP" if ok else "A11_REVIEW_REQUIRED",
        "live_note": "Bu A11 kapanışı local/repo kalite kanıtıdır. Canlı ortam için ayrıca canlı smoke ve servis log kontrolü yapılmalıdır.",
    }

    write_reports(
        preliminary_result,
        pytest_summary,
        strict_unraisable_summary,
        strict_resource_summary,
        warning_lines,
    )

    evidence_files = collect_evidence_files()

    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in evidence_files:
            zf.write(path, rel(path))

    with zipfile.ZipFile(OUT_ZIP, "r") as zf:
        names = zf.namelist()

    duplicates = sorted([name for name, count in Counter(names).items() if count > 1])
    sha = hashlib.sha256(OUT_ZIP.read_bytes()).hexdigest()

    final_result = {
        **preliminary_result,
        "evidence_zip_sha256": sha,
        "evidence_file_count": len(evidence_files),
        "zip_entry_count": len(names),
        "duplicate_zip_entry_count": len(duplicates),
        "duplicate_zip_entries": duplicates,
    }

    final_result["ok"] = bool(ok and not duplicates)
    final_result["decision"] = "accepted_warning_zero" if final_result["ok"] else "blocked_manual_review"
    final_result["next_phase"] = "A12_UI_TECHNICAL_LANGUAGE_CLEANUP" if final_result["ok"] else "A11_REVIEW_REQUIRED"

    write_reports(
        final_result,
        pytest_summary,
        strict_unraisable_summary,
        strict_resource_summary,
        warning_lines,
    )

    print("A11C_REPORT_JSON:", OUT_JSON)
    print("A11C_REPORT_MD:", OUT_MD)
    print("A11C_EVIDENCE_ZIP:", OUT_ZIP)
    print("A11C_EVIDENCE_ZIP_SHA256:", sha)
    print("A11C_SOURCE_A11B2_OK:", final_result["source_a11b2_ok"])
    print("A11C_COMPILEALL_RETURN_CODE:", final_result["compileall_returncode"])
    print("A11C_PYTEST_RETURN_CODE:", final_result["pytest_returncode"])
    print("A11C_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A11C_STRICT_UNRAISABLE_RETURN_CODE:", final_result["strict_unraisable_returncode"])
    print("A11C_STRICT_UNRAISABLE_SUMMARY:", json.dumps(strict_unraisable_summary, ensure_ascii=False))
    print("A11C_STRICT_RESOURCE_RETURN_CODE:", final_result["strict_resource_returncode"])
    print("A11C_STRICT_RESOURCE_SUMMARY:", json.dumps(strict_resource_summary, ensure_ascii=False))
    print("A11C_WARNINGS_AFTER:", final_result["warnings_after"])
    print("A11C_DUPLICATE_ZIP_ENTRY_COUNT:", final_result["duplicate_zip_entry_count"])
    print("A11C_OK:", final_result["ok"])

    return 0 if final_result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
