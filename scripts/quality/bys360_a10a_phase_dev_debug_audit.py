from pathlib import Path
from datetime import datetime
import json
import re

ROOT = Path(".").resolve()

OUT_JSON = Path("reports/quality/BYS360_A10A_PHASE_DEV_DEBUG_AUDIT.json")
OUT_MD = Path("reports/quality/BYS360_A10A_PHASE_DEV_DEBUG_AUDIT.md")

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "reports",
    "logs",
    "backups",
    "dist",
    "build",
    ".mypy_cache",
    ".tox",
}

SCAN_ROOTS = [
    "app",
    "tests",
    "scripts",
    "migrations",
    "mobile",
    "mobile_flutter",
    "templates",
    "static",
]

TEXT_EXTENSIONS = {
    ".py", ".ps1", ".html", ".jinja", ".jinja2", ".js", ".ts", ".css",
    ".scss", ".dart", ".json", ".yaml", ".yml", ".md", ".txt", ".sql",
}

USER_FACING_EXTENSIONS = {
    ".html", ".jinja", ".jinja2", ".js", ".ts", ".css", ".scss", ".dart",
}

NAME_PATTERNS = [
    "phase",
    "faz",
    "dev",
    "debug",
    "tmp",
    "temp",
    "draft",
    "old",
    "bak",
    "disabled",
    "legacy",
    "sync",
    "workflow",
    "overlay",
    "claude",
    "hotfix",
    "repair",
]

TECHNICAL_UI_TERMS = [
    "phase",
    "faz",
    "sync",
    "workflow",
    "debug",
    "endpoint",
    "unauthorized_scope",
    "stacktrace",
    "traceback",
    "exception",
    "raw error",
    "api error",
    "json",
    "gate",
    "contract",
    "pytest",
    "ruff",
    "compileall",
]

PROTECTED_KEEP_PATHS = {
    "scripts/windows/claude_phase7_final_quality.ps1",
    "scripts/quality/bys360_a85g_repo_cleanup_audit.py",
    "scripts/windows/a8_live_cutover_guard.ps1",
    "scripts/windows/pre_live_backup_plan.ps1",
}

PROTECTED_KEEP_NAME_HINTS = {
    "claude_phase7_final_quality.ps1",
    "a8_live_cutover_guard.ps1",
    "pre_live_backup_plan.ps1",
}

def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & EXCLUDE_DIRS)

def iter_files():
    seen = set()
    for root_name in SCAN_ROOTS:
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if is_excluded(path):
                continue
            r = rel(path)
            if r in seen:
                continue
            seen.add(r)
            yield path

def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > 2_000_000:
            return ""
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return ""

def name_hits(path: Path):
    r = rel(path).lower()
    name = path.name.lower()
    hits = []
    for pattern in NAME_PATTERNS:
        if pattern in name or f"/{pattern}" in r or f"_{pattern}" in r or f"-{pattern}" in r:
            hits.append(pattern)
    return sorted(set(hits))

def technical_ui_hits(path: Path):
    if path.suffix.lower() not in USER_FACING_EXTENSIONS:
        return []
    text = read_text(path)
    if not text:
        return []

    hits = []
    lower = text.lower()
    lines = text.splitlines()

    for term in TECHNICAL_UI_TERMS:
        if term.lower() in lower:
            term_hits = []
            for i, line in enumerate(lines, start=1):
                if term.lower() in line.lower():
                    term_hits.append({
                        "line": i,
                        "term": term,
                        "sample": line.strip()[:240],
                    })
                    if len(term_hits) >= 10:
                        break
            hits.extend(term_hits)

    return hits

def classify_path(path: Path, hits):
    r = rel(path)
    name = path.name

    if r in PROTECTED_KEEP_PATHS or name in PROTECTED_KEEP_NAME_HINTS:
        return "protected_keep"

    if "/tests/" in f"/{r}" or r.startswith("tests/"):
        return "test_or_contract_review"

    if r.startswith("scripts/quality/"):
        return "quality_gate_review"

    if r.startswith("scripts/windows/"):
        return "windows_script_review"

    if r.startswith("app/") or r.startswith("templates/") or r.startswith("static/") or r.startswith("mobile"):
        return "app_user_or_runtime_review"

    return "general_review"

def main():
    file_candidates = []
    protected_matches = []
    ui_technical_hits = []
    critical_keep_missing = []

    for keep in sorted(PROTECTED_KEEP_PATHS):
        if not (ROOT / keep).exists():
            critical_keep_missing.append(keep)

    for path in iter_files():
        r = rel(path)
        hits = name_hits(path)

        if hits:
            item = {
                "path": r,
                "name": path.name,
                "suffix": path.suffix.lower(),
                "hits": hits,
                "classification": classify_path(path, hits),
            }

            if item["classification"] == "protected_keep":
                protected_matches.append(item)
            else:
                file_candidates.append(item)

        ui_hits = technical_ui_hits(path)
        if ui_hits:
            ui_technical_hits.append({
                "path": r,
                "suffix": path.suffix.lower(),
                "hits": ui_hits[:20],
                "hit_count": len(ui_hits),
            })

    by_class = {}
    for item in file_candidates:
        by_class[item["classification"]] = by_class.get(item["classification"], 0) + 1

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10A_PHASE_DEV_DEBUG_AUDIT",
        "mode": "audit_only",
        "file_candidate_count": len(file_candidates),
        "protected_match_count": len(protected_matches),
        "critical_keep_missing_count": len(critical_keep_missing),
        "ui_technical_file_count": len(ui_technical_hits),
        "ui_technical_hit_total": sum(x["hit_count"] for x in ui_technical_hits),
        "by_classification": by_class,
        "critical_keep_missing": critical_keep_missing,
        "protected_matches": protected_matches,
        "file_candidates": file_candidates[:1000],
        "ui_technical_hits": ui_technical_hits[:500],
        "ok": (
            len(file_candidates) == 0
            and len(ui_technical_hits) == 0
            and len(critical_keep_missing) == 0
        ),
        "next_action": "A10B sınıflandırma/koruma listesi ve güvenli karantina planı hazırlanmalı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10A Faz / Dev / Debug / Teknik Dil Audit",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Özet",
        "",
        f"- Mode: `{result['mode']}`",
        f"- File candidate count: {result['file_candidate_count']}",
        f"- Protected match count: {result['protected_match_count']}",
        f"- Critical keep missing count: {result['critical_keep_missing_count']}",
        f"- UI technical file count: {result['ui_technical_file_count']}",
        f"- UI technical hit total: {result['ui_technical_hit_total']}",
        f"- A10A OK: {result['ok']}",
        "",
        "## Sınıflandırma",
        "",
        "```json",
        json.dumps(result["by_classification"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Eksik Korunması Gereken Dosyalar",
        "",
        "```text",
        "\n".join(result["critical_keep_missing"]) if result["critical_keep_missing"] else "Yok",
        "```",
        "",
        "## Korunan Eşleşmeler",
        "",
        "```json",
        json.dumps(result["protected_matches"][:80], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Dosya Adı / Yol Adayları İlk 250",
        "",
        "```json",
        json.dumps(result["file_candidates"][:250], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Kullanıcıya Yansıyabilecek Teknik Dil Bulguları İlk 150",
        "",
        "```json",
        json.dumps(result["ui_technical_hits"][:150], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Not",
        "",
        "Bu rapor dosya silmez veya taşımaz. Adaylar manuel/kurallı sınıflandırmadan sonra A10B aşamasında karantina ya da düzeltme planına alınacaktır.",
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A10A_REPORT_JSON:", OUT_JSON)
    print("A10A_REPORT_MD:", OUT_MD)
    print("A10A_FILE_CANDIDATE_COUNT:", result["file_candidate_count"])
    print("A10A_PROTECTED_MATCH_COUNT:", result["protected_match_count"])
    print("A10A_CRITICAL_KEEP_MISSING_COUNT:", result["critical_keep_missing_count"])
    print("A10A_UI_TECHNICAL_FILE_COUNT:", result["ui_technical_file_count"])
    print("A10A_UI_TECHNICAL_HIT_TOTAL:", result["ui_technical_hit_total"])
    print("A10A_OK:", result["ok"])

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
