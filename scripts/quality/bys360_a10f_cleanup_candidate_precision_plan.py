from pathlib import Path
from datetime import datetime
import json
import re

ROOT = Path(".").resolve()

A10B_JSON = Path("reports/quality/BYS360_A10B_PHASE_DEV_DEBUG_PRECISION_AUDIT.json")
A10E_JSON = Path("reports/quality/BYS360_A10E_HARD_UI_FALSE_POSITIVE_CLOSE_DECISION.json")

OUT_JSON = Path("reports/quality/BYS360_A10F_CLEANUP_CANDIDATE_PRECISION_PLAN.json")
OUT_MD = Path("reports/quality/BYS360_A10F_CLEANUP_CANDIDATE_PRECISION_PLAN.md")

PROTECTED_PATHS = {
    "scripts/windows/claude_phase7_final_quality.ps1",
    "scripts/windows/a8_live_cutover_guard.ps1",
    "scripts/windows/pre_live_backup_plan.ps1",
    "scripts/quality/bys360_a85g_repo_cleanup_audit.py",
}

PROTECTED_PREFIXES = [
    "app/",
    "templates/",
    "static/",
    "mobile/",
    "mobile_flutter/",
    "migrations/",
    "tests/",
    "scripts/quality/",
]

RUNTIME_PREFIXES = [
    "app/",
    "templates/",
    "static/",
    "mobile/",
    "mobile_flutter/",
    "migrations/",
]

TEXT_EXTENSIONS = {
    ".py", ".ps1", ".html", ".jinja", ".jinja2", ".js", ".ts", ".css",
    ".scss", ".dart", ".json", ".yaml", ".yml", ".md", ".txt", ".sql",
}

REFERENCE_SCAN_ROOTS = [
    "app",
    "tests",
    "scripts",
    "migrations",
    "mobile",
    "mobile_flutter",
    "templates",
    "static",
]

REFERENCE_EXCLUDE_DIRS = {
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
}

SAFE_QUARANTINE_HINTS = [
    "old",
    "bak",
    "draft",
    "disabled",
    "tmp",
    "temp",
    "overlay",
    "hotfix",
    "repair",
    "debug",
]

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))

def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def is_excluded(path: Path) -> bool:
    return bool(set(path.parts) & REFERENCE_EXCLUDE_DIRS)

def read_text(path: Path):
    try:
        if not path.exists() or path.stat().st_size > 2_000_000:
            return ""
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return ""

def iter_reference_files():
    for root_name in REFERENCE_SCAN_ROOTS:
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if is_excluded(path):
                continue
            if path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            yield path

def build_reference_index():
    indexed = []
    for path in iter_reference_files():
        text = read_text(path)
        if text:
            indexed.append((rel(path), text))
    return indexed

def reference_count(candidate_path: str, index):
    p = Path(candidate_path)
    stem = p.stem
    name = p.name
    module_like = candidate_path.replace("/", ".").replace("\\", ".")
    if module_like.endswith(".py"):
        module_like = module_like[:-3]

    needles = sorted(set([
        candidate_path,
        candidate_path.replace("/", "\\"),
        name,
        stem,
        module_like,
    ]), key=len, reverse=True)

    refs = []
    for file_path, text in index:
        if file_path == candidate_path:
            continue
        hit_terms = []
        for needle in needles:
            if needle and needle in text:
                hit_terms.append(needle)
        if hit_terms:
            refs.append({
                "path": file_path,
                "hit_terms": hit_terms[:5],
            })
            if len(refs) >= 30:
                break
    return refs

def classify_candidate(item, refs):
    path = item.get("path", "")
    low = path.lower()
    hits = set(item.get("hits", []))
    cls = item.get("a10b_classification")

    if path in PROTECTED_PATHS:
        return "protected_keep"

    if cls == "runtime_cleanup_review":
        return "runtime_keep_rename_later"

    if any(low.startswith(prefix) for prefix in RUNTIME_PREFIXES):
        return "runtime_keep_manual_review"

    if refs:
        return "referenced_keep_review"

    if any(low.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        return "protected_prefix_keep_review"

    if hits & set(SAFE_QUARANTINE_HINTS):
        return "safe_quarantine_candidate"

    return "manual_review"

def main():
    if not A10B_JSON.exists():
        raise SystemExit("A10B raporu bulunamadı. Önce A10B çalışmalı.")

    a10b = read_json(A10B_JSON)
    a10e = read_json(A10E_JSON) if A10E_JSON.exists() else {}

    cleanup_candidates = a10b.get("cleanup_candidates", [])
    index = build_reference_index()

    planned = []
    by_class = {}

    for item in cleanup_candidates:
        path = item.get("path", "")
        refs = reference_count(path, index)
        final_class = classify_candidate(item, refs)

        row = dict(item)
        row["reference_count"] = len(refs)
        row["references_sample"] = refs[:10]
        row["a10f_decision"] = final_class

        planned.append(row)
        by_class[final_class] = by_class.get(final_class, 0) + 1

    safe_quarantine = [x for x in planned if x["a10f_decision"] == "safe_quarantine_candidate"]
    keep_or_review = [x for x in planned if x["a10f_decision"] != "safe_quarantine_candidate"]

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10F_CLEANUP_CANDIDATE_PRECISION_PLAN",
        "mode": "plan_only",
        "source_a10b": str(A10B_JSON),
        "a10e_ok": a10e.get("ok"),
        "cleanup_candidate_count": len(cleanup_candidates),
        "safe_quarantine_candidate_count": len(safe_quarantine),
        "keep_or_review_count": len(keep_or_review),
        "by_decision": by_class,
        "safe_quarantine_candidates": safe_quarantine[:500],
        "keep_or_review": keep_or_review[:800],
        "ok": len(cleanup_candidates) == 0,
        "next_action": "A10G aşamasında yalnızca safe_quarantine_candidate sınıfı yedekli karantinaya alınmalı; runtime dosyalara dokunulmamalı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10F Cleanup Candidate Precision Plan",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Özet",
        "",
        f"- A10E OK: {result['a10e_ok']}",
        f"- Cleanup candidate count: {result['cleanup_candidate_count']}",
        f"- Safe quarantine candidate count: {result['safe_quarantine_candidate_count']}",
        f"- Keep or review count: {result['keep_or_review_count']}",
        f"- A10F OK: {result['ok']}",
        "",
        "## Karar Dağılımı",
        "",
        "```json",
        json.dumps(result["by_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Güvenli Karantina Adayları İlk 250",
        "",
        "```json",
        json.dumps(result["safe_quarantine_candidates"][:250], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Korunacak / İncelenecek İlk 250",
        "",
        "```json",
        json.dumps(result["keep_or_review"][:250], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Not",
        "",
        "Bu rapor dosya silmez, taşımaz veya değiştirmez. Runtime, migration, template, mobile ve referans alan dosyalar karantinaya alınmaz.",
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A10F_REPORT_JSON:", OUT_JSON)
    print("A10F_REPORT_MD:", OUT_MD)
    print("A10F_CLEANUP_CANDIDATE_COUNT:", result["cleanup_candidate_count"])
    print("A10F_SAFE_QUARANTINE_CANDIDATE_COUNT:", result["safe_quarantine_candidate_count"])
    print("A10F_KEEP_OR_REVIEW_COUNT:", result["keep_or_review_count"])
    print("A10F_A10E_OK:", result["a10e_ok"])
    print("A10F_OK:", result["ok"])

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
