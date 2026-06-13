from pathlib import Path
from datetime import datetime
import json
import re

ROOT = Path(".").resolve()

A10A_JSON = Path("reports/quality/BYS360_A10A_PHASE_DEV_DEBUG_AUDIT.json")
OUT_JSON = Path("reports/quality/BYS360_A10B_PHASE_DEV_DEBUG_PRECISION_AUDIT.json")
OUT_MD = Path("reports/quality/BYS360_A10B_PHASE_DEV_DEBUG_PRECISION_AUDIT.md")

FALSE_POSITIVE_NAME_WORDS = [
    "template",
    "development",
    "developer_comment_cleanup",
    "devamsizlik",
    "devamsızlık",
]

PROTECTED_KEEP_PATHS = {
    "scripts/windows/claude_phase7_final_quality.ps1",
    "scripts/quality/bys360_a85g_repo_cleanup_audit.py",
    "scripts/windows/a8_live_cutover_guard.ps1",
    "scripts/windows/pre_live_backup_plan.ps1",
}

PROTECTED_PREFIXES = [
    "scripts/quality/",
    "tests/",
]

RUNTIME_RENAME_PATTERNS = [
    "phase",
    "faz",
]

TRUE_CLEANUP_NAME_PATTERNS = [
    "debug",
    "tmp",
    "temp",
    "draft",
    "old",
    "bak",
    "disabled",
    "overlay",
    "hotfix",
    "repair",
]

TECHNICAL_UI_HARD_TERMS = [
    "traceback",
    "stacktrace",
    "unauthorized_scope",
    "raw error",
    "api error",
    "exception",
    "pytest",
    "ruff",
    "compileall",
    "endpoint",
    "workflow state",
]

TECHNICAL_UI_REVIEW_TERMS = [
    "phase",
    "faz",
    "sync",
    "workflow",
    "gate",
    "contract",
    "json",
    "debug",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))


def is_false_positive_name(path: str) -> bool:
    low = path.lower()
    return any(word in low for word in FALSE_POSITIVE_NAME_WORDS)


def classify_file(item):
    path = item["path"]
    low = path.lower()
    hits = set(item.get("hits", []))

    if path in PROTECTED_KEEP_PATHS:
        return "protected_keep"

    if any(low.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        return "contract_or_quality_keep_review"

    if is_false_positive_name(path):
        return "likely_false_positive_name"

    if low.startswith("app/") or low.startswith("templates/") or low.startswith("static/") or low.startswith("mobile"):
        if hits & set(RUNTIME_RENAME_PATTERNS):
            return "runtime_rename_candidate"
        if hits & set(TRUE_CLEANUP_NAME_PATTERNS):
            return "runtime_cleanup_review"
        return "runtime_review"

    if low.startswith("scripts/windows/"):
        if hits & {"repair", "hotfix", "overlay"}:
            return "windows_legacy_script_cleanup_candidate"
        return "windows_script_review"

    if hits & set(TRUE_CLEANUP_NAME_PATTERNS):
        return "cleanup_candidate"

    return "review"


def classify_ui_hit(hit_item):
    hard = []
    review = []
    likely_false_positive = []

    for hit in hit_item.get("hits", []):
        term = str(hit.get("term", "")).lower()
        sample = str(hit.get("sample", "")).lower()

        if any(t in term or t in sample for t in TECHNICAL_UI_HARD_TERMS):
            hard.append(hit)
        elif any(t in term or t in sample for t in TECHNICAL_UI_REVIEW_TERMS):
            if "json.stringify" in sample or "application/json" in sample:
                likely_false_positive.append(hit)
            else:
                review.append(hit)
        else:
            review.append(hit)

    if hard:
        classification = "ui_hard_technical_language"
    elif review:
        classification = "ui_review_technical_language"
    else:
        classification = "ui_likely_false_positive"

    return {
        "path": hit_item["path"],
        "classification": classification,
        "hard_count": len(hard),
        "review_count": len(review),
        "likely_false_positive_count": len(likely_false_positive),
        "hard_hits": hard[:20],
        "review_hits": review[:20],
        "likely_false_positive_hits": likely_false_positive[:10],
    }


def main():
    if not A10A_JSON.exists():
        raise SystemExit("A10A raporu bulunamadı. Önce A10A çalışmalı.")

    a10a = read_json(A10A_JSON)

    classified_files = []
    by_class = {}

    for item in a10a.get("file_candidates", []):
        cls = classify_file(item)
        row = dict(item)
        row["a10b_classification"] = cls
        classified_files.append(row)
        by_class[cls] = by_class.get(cls, 0) + 1

    classified_ui = []
    ui_by_class = {}

    for item in a10a.get("ui_technical_hits", []):
        row = classify_ui_hit(item)
        classified_ui.append(row)
        cls = row["classification"]
        ui_by_class[cls] = ui_by_class.get(cls, 0) + 1

    hard_ui_files = [x for x in classified_ui if x["classification"] == "ui_hard_technical_language"]
    rename_candidates = [x for x in classified_files if x["a10b_classification"] == "runtime_rename_candidate"]
    cleanup_candidates = [
        x for x in classified_files
        if x["a10b_classification"] in {
            "windows_legacy_script_cleanup_candidate",
            "cleanup_candidate",
            "runtime_cleanup_review",
        }
    ]

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10B_PHASE_DEV_DEBUG_PRECISION_AUDIT",
        "mode": "audit_only",
        "source_a10a": str(A10A_JSON),
        "a10a_file_candidate_count": a10a.get("file_candidate_count"),
        "a10a_ui_technical_file_count": a10a.get("ui_technical_file_count"),
        "file_by_classification": by_class,
        "ui_by_classification": ui_by_class,
        "runtime_rename_candidate_count": len(rename_candidates),
        "cleanup_candidate_count": len(cleanup_candidates),
        "hard_ui_technical_file_count": len(hard_ui_files),
        "classified_files": classified_files[:1500],
        "classified_ui": classified_ui[:800],
        "runtime_rename_candidates": rename_candidates[:500],
        "cleanup_candidates": cleanup_candidates[:500],
        "hard_ui_files": hard_ui_files[:300],
        "ok": (
            len(rename_candidates) == 0
            and len(cleanup_candidates) == 0
            and len(hard_ui_files) == 0
        ),
        "next_action": "A10C: önce hard UI teknik dil düzeltmeleri ve güvenli rename/compat planı hazırlanmalı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10B Hassas Faz / Dev / Debug Sınıflandırma Audit",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Özet",
        "",
        f"- A10A file candidate count: {result['a10a_file_candidate_count']}",
        f"- A10A UI technical file count: {result['a10a_ui_technical_file_count']}",
        f"- Runtime rename candidate count: {result['runtime_rename_candidate_count']}",
        f"- Cleanup candidate count: {result['cleanup_candidate_count']}",
        f"- Hard UI technical file count: {result['hard_ui_technical_file_count']}",
        f"- A10B OK: {result['ok']}",
        "",
        "## Dosya Sınıflandırması",
        "",
        "```json",
        json.dumps(result["file_by_classification"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## UI Teknik Dil Sınıflandırması",
        "",
        "```json",
        json.dumps(result["ui_by_classification"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Runtime Rename Adayları İlk 200",
        "",
        "```json",
        json.dumps(result["runtime_rename_candidates"][:200], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Cleanup Adayları İlk 200",
        "",
        "```json",
        json.dumps(result["cleanup_candidates"][:200], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Hard UI Teknik Dil Dosyaları İlk 120",
        "",
        "```json",
        json.dumps(result["hard_ui_files"][:120], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Not",
        "",
        "Bu rapor dosya silmez, taşımaz veya değiştirmez. A10C aşamasında yalnızca güvenli düzeltme planı hazırlanacaktır.",
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A10B_REPORT_JSON:", OUT_JSON)
    print("A10B_REPORT_MD:", OUT_MD)
    print("A10B_RUNTIME_RENAME_CANDIDATE_COUNT:", result["runtime_rename_candidate_count"])
    print("A10B_CLEANUP_CANDIDATE_COUNT:", result["cleanup_candidate_count"])
    print("A10B_HARD_UI_TECHNICAL_FILE_COUNT:", result["hard_ui_technical_file_count"])
    print("A10B_OK:", result["ok"])

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
