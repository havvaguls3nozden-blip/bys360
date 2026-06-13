from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter
import json
import os
import re
import shutil
import subprocess

ROOT = Path(".").resolve()
QUALITY = ROOT / "reports" / "quality"
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

A12D_JSON = QUALITY / "BYS360_A12D_UI_TECHNICAL_LANGUAGE_FULL_SCOPE_GATE.json"

OUT_JSON = QUALITY / "BYS360_A12E_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP.json"
OUT_MD = QUALITY / "BYS360_A12E_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP.md"
BACKUP_ROOT = RELEASES / f"A12E_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP_BACKUP_{STAMP}"

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


def is_false_positive(text: str) -> bool:
    low = text.lower()
    return any(x.lower() in low for x in FALSE_POSITIVE_HINTS)


def mask_jinja(text: str):
    masks = []

    def repl(match):
        token = f"__BYS360_JINJA_MASK_{len(masks)}__"
        masks.append((token, match.group(0)))
        return token

    masked = re.sub(r"({{.*?}}|{%.*?%}|{#.*?#})", repl, text)
    return masked, masks


def unmask_jinja(text: str, masks):
    for token, original in masks:
        text = text.replace(token, original)
    return text


def replace_terms(segment: str) -> str:
    replacements = [
        ("Hotfix ve rollback kararı yazılı kayıtla yönetilir.", "Acil düzeltme ve geri dönüş kararı yazılı kayıtla yönetilir."),
        ("SQL hotfix dosyası", "Veri düzeltme dosyası"),
        ("Son hotfix kayıtları", "Son acil düzeltme kayıtları"),
        ("Henüz hotfix kaydı bulunmuyor.", "Henüz acil düzeltme kaydı bulunmuyor."),
        ("Hotfix kaydı", "Acil düzeltme kaydı"),
        ("Hotfix kaydet", "Acil düzeltme kaydet"),
        ("route ve backend yetki kontrolleri", "sayfa ve sistem yetki kontrolleri"),
        ("backend yetki", "sistem yetki"),
        ("backend", "sistem"),
        ("rollback", "geri dönüş"),
        ("Rollback", "Geri dönüş"),
        ("endpoint", "sistem bağlantısı"),
        ("Endpoint", "Sistem bağlantısı"),
        ("database error", "veri kaydı hatası"),
        ("Database error", "Veri kaydı hatası"),
        ("Internal Server Error", "Sistem hatası"),
        ("Stack trace", "hata ayrıntısı"),
        ("Traceback", "hata ayrıntısı"),
        ("SQLAlchemy", "veri katmanı"),
        ("Alembic", "veri geçiş sistemi"),
        ("Exception", "hata kaydı"),
        ("csrf token", "güvenlik doğrulaması"),
        ("CSRF token", "güvenlik doğrulaması"),
        ("unauthorized_scope", "yetki kapsamı dışında"),
        ("workflow state", "süreç durumu"),
        ("phase sync", "süreç eşitleme"),
        ("migration görünürlüğü", "kayıt görünürlüğü"),
        ("Migration zinciri", "Veri geçiş zinciri"),
        ("migration zinciri", "veri geçiş zinciri"),
        ("Migration", "Veri geçişi"),
        ("migration", "veri geçişi"),
        (".env yolu", "Ayar dosyası yolu"),
        (".env içinde", "Ortam ayarlarında"),
        (".env", "ayar dosyası"),
        ("env sertleştirmesi", "ortam ayarları"),
        ("Faz gate", "Kontrol listesi"),
        ("faz gate", "kontrol listesi"),
        ("gate izleme", "kontrol izleme"),
        ("gate", "kontrol"),
    ]

    for old, new in replacements:
        segment = segment.replace(old, new)

    segment = re.sub(r"\bFaz\s+(\d+)\b", r"Kontrol \1", segment)
    segment = re.sub(r"\bfaz\s+(\d+)\b", r"kontrol \1", segment)
    segment = re.sub(r"\bPhase\s+(\d+)\b", r"Kontrol \1", segment)
    segment = re.sub(r"\bphase\s+(\d+)\b", r"kontrol \1", segment)

    segment = re.sub(r"\bFaz\b", "Kontrol", segment)
    segment = re.sub(r"\bfaz\b", "kontrol", segment)
    segment = re.sub(r"\bPhase\b", "Kontrol", segment)
    segment = re.sub(r"\bphase\b", "kontrol", segment)

    segment = re.sub(r"\bA10\b", "Kontrol 10", segment)
    segment = re.sub(r"\bA11\b", "Kontrol 11", segment)
    segment = re.sub(r"\bA12\b", "Kontrol 12", segment)

    segment = re.sub(r"(?<![A-Za-zÇĞİÖŞÜçğıöşü])env(?![A-Za-zÇĞİÖŞÜçğıöşü])", "ortam ayarı", segment)

    return segment


def transform_html_line(line: str) -> str:
    masked, masks = mask_jinja(line)

    def text_node_repl(match):
        return match.group(1) + replace_terms(match.group(2)) + match.group(3)

    masked = re.sub(r"(>)([^<]+)(<)", text_node_repl, masked)

    for attr in VISIBLE_ATTRS:
        pattern = rf"({re.escape(attr)}\s*=\s*)([\"'])(.*?)(\2)"

        def attr_repl(match):
            return match.group(1) + match.group(2) + replace_terms(match.group(3)) + match.group(4)

        masked = re.sub(pattern, attr_repl, masked, flags=re.IGNORECASE)

    return unmask_jinja(masked, masks)


def transform_string_literals(line: str) -> str:
    masked, masks = mask_jinja(line)

    def repl(match):
        quote = match.group(1)
        body = match.group(2)
        return quote + replace_terms(body) + quote

    masked = re.sub(r"(['\"])(.*?)(?<!\\)\1", repl, masked)
    return unmask_jinja(masked, masks)


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


def transform_line(path: Path, line: str) -> str:
    if not is_probably_visible(path, line):
        return line

    suffix = path.suffix.lower()

    if suffix in {".html", ".jinja", ".jinja2"}:
        return transform_html_line(line)

    if suffix in {".js", ".py"}:
        return transform_string_literals(line)

    return line


def visible_segments_from_html(line: str) -> list[str]:
    masked, _ = mask_jinja(line)
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
    masked, _ = mask_jinja(line)
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
        if term == "env":
            if re.search(r"(?<![A-Za-zÇĞİÖŞÜçğıöşü])env(?![A-Za-zÇĞİÖŞÜçğıöşü])", segment):
                hits.append(term)
            continue

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


def collect_target_paths(a12d: dict) -> list[Path]:
    paths = set()

    for item in a12d.get("visible_candidates", []):
        raw = item.get("path")
        if raw:
            paths.add(ROOT / raw)

    for root in SCAN_ROOTS:
        if root.exists():
            for path in root.rglob("*"):
                if should_scan(path):
                    text = path.read_text(encoding="utf-8-sig", errors="ignore")
                    if any(phrase in text for phrase in KNOWN_CLEANED_PHRASES):
                        paths.add(path)

    return sorted([p for p in paths if p.exists() and p.is_file()])


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)
    RELEASES.mkdir(parents=True, exist_ok=True)

    a12d = read_json(A12D_JSON)
    target_paths = collect_target_paths(a12d)

    operations = []
    total_replacements = 0

    for path in target_paths:
        original = path.read_text(encoding="utf-8-sig", errors="ignore")
        lines = original.splitlines(keepends=True)

        new_lines = []
        file_replacements = 0

        for line in lines:
            ending = ""
            core = line
            if line.endswith("\r\n"):
                core = line[:-2]
                ending = "\r\n"
            elif line.endswith("\n"):
                core = line[:-1]
                ending = "\n"

            changed = transform_line(path, core)
            if changed != core:
                file_replacements += 1

            new_lines.append(changed + ending)

        updated = "".join(new_lines)

        if updated != original:
            backup_path = BACKUP_ROOT / path.relative_to(ROOT)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup_path)
            path.write_text(updated, encoding="utf-8")

            total_replacements += file_replacements
            operations.append({
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "status": "patched",
                "changed_line_count": file_replacements,
                "backup": str(backup_path),
            })
        else:
            operations.append({
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "status": "unchanged",
                "changed_line_count": 0,
            })

    post_candidates = scan_visible_candidates()
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

    by_term = Counter(item["term"] for item in post_candidates)
    by_path = Counter(item["path"] for item in post_candidates)

    ok = (
        tests_ok
        and len(post_candidates) == 0
        and len(remaining_known) == 0
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A12E_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP",
        "ok": ok,
        "decision": "A12E_SAFE_CLEANUP_GREEN" if ok else "A12E_REVIEW_REMAINING_CANDIDATES",
        "source_a12d_visible_candidate_count": a12d.get("visible_candidate_count"),
        "target_file_count": len(target_paths),
        "operation_count": len(operations),
        "total_changed_line_count": total_replacements,
        "backup_root": str(BACKUP_ROOT),
        "post_visible_candidate_count": len(post_candidates),
        "remaining_known_cleaned_phrase_count": len(remaining_known),
        "post_candidate_by_term": dict(by_term),
        "post_candidate_by_path_top_80": dict(by_path.most_common(80)),
        "post_visible_candidates": post_candidates[:1000],
        "remaining_known_cleaned_phrases": remaining_known,
        "compileall_returncode": compile_result["returncode"],
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "operations": operations,
        "next_action": "A12F final evidence paketine geçilebilir." if ok else "Kalan adaylar incelenerek A12E2 güvenli temizlik yapılmalı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 A12E UI Teknik Dil Güvenli Temizlik",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Source A12D visible candidate count: {result['source_a12d_visible_candidate_count']}",
        f"- Target file count: {result['target_file_count']}",
        f"- Total changed line count: {result['total_changed_line_count']}",
        f"- Backup root: `{result['backup_root']}`",
        f"- Post visible candidate count: {result['post_visible_candidate_count']}",
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
        "## Post Candidate by Term",
        "",
        "```json",
        json.dumps(result["post_candidate_by_term"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Post Candidate by Path",
        "",
        "```json",
        json.dumps(result["post_candidate_by_path_top_80"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Remaining Known Cleaned Phrases",
        "",
        "```json",
        json.dumps(remaining_known, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Post Visible Candidates",
        "",
        "```json",
        json.dumps(result["post_visible_candidates"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Operations",
        "",
        "```json",
        json.dumps(operations, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("A12E_REPORT_JSON:", OUT_JSON)
    print("A12E_REPORT_MD:", OUT_MD)
    print("A12E_BACKUP_ROOT:", BACKUP_ROOT)
    print("A12E_TARGET_FILE_COUNT:", result["target_file_count"])
    print("A12E_TOTAL_CHANGED_LINE_COUNT:", result["total_changed_line_count"])
    print("A12E_POST_VISIBLE_CANDIDATE_COUNT:", result["post_visible_candidate_count"])
    print("A12E_REMAINING_KNOWN_CLEANED_PHRASE_COUNT:", result["remaining_known_cleaned_phrase_count"])
    print("A12E_POST_CANDIDATE_BY_TERM:", json.dumps(result["post_candidate_by_term"], ensure_ascii=False))
    print("A12E_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A12E_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A12E_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A12E_OK:", result["ok"])

    return 0 if tests_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
