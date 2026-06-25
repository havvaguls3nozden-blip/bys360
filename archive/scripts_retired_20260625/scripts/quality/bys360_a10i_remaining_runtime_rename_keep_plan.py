from pathlib import Path
from datetime import datetime
import json
import re

ROOT = Path(".").resolve()

A10F_JSON = Path("reports/quality/BYS360_A10F_CLEANUP_CANDIDATE_PRECISION_PLAN.json")
OUT_JSON = Path("reports/quality/BYS360_A10I_REMAINING_RUNTIME_RENAME_KEEP_PLAN.json")
OUT_MD = Path("reports/quality/BYS360_A10I_REMAINING_RUNTIME_RENAME_KEEP_PLAN.md")

RENAME_WORDS = {
    "phase": "module",
    "faz": "module",
    "hotfix": "maintenance",
    "repair": "maintenance",
    "debug": "diagnostics",
    "legacy": "compat",
}

RISK_PREFIXES = [
    "app/",
    "migrations/",
    "mobile_flutter/",
    "mobile/",
    "templates/",
    "static/",
]

TEXT_EXTENSIONS = {
    ".py", ".ps1", ".html", ".jinja", ".jinja2", ".js", ".ts", ".css",
    ".scss", ".dart", ".json", ".yaml", ".yml", ".md", ".txt", ".sql",
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

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", ".ruff_cache", "reports", "logs", "backups",
    "dist", "build",
}

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))

def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def is_excluded(path: Path):
    return bool(set(path.parts) & EXCLUDE_DIRS)

def read_text(path: Path):
    try:
        if not path.exists() or path.stat().st_size > 2_000_000:
            return ""
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return ""

def iter_files():
    for root_name in SCAN_ROOTS:
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

def suggested_name(path: str):
    p = Path(path)
    name = p.name
    new_name = name
    for old, new in RENAME_WORDS.items():
        new_name = re.sub(old, new, new_name, flags=re.I)
    if new_name == name:
        return None
    return str(p.with_name(new_name)).replace("\\", "/")

def find_references(path: str):
    p = Path(path)
    stem = p.stem
    name = p.name
    module_like = path.replace("/", ".").replace("\\", ".")
    if module_like.endswith(".py"):
        module_like = module_like[:-3]

    needles = sorted(set([
        path,
        path.replace("/", "\\"),
        name,
        stem,
        module_like,
    ]), key=len, reverse=True)

    refs = []
    for file in iter_files():
        r = rel(file)
        if r == path:
            continue
        text = read_text(file)
        if not text:
            continue
        hit_terms = [needle for needle in needles if needle and needle in text]
        if hit_terms:
            refs.append({
                "path": r,
                "hit_terms": hit_terms[:5],
            })
            if len(refs) >= 50:
                break
    return refs

def classify_remaining(item, refs):
    path = item.get("path", "")
    low = path.lower()
    a10f_decision = item.get("a10f_decision", "")

    if a10f_decision == "referenced_keep_review":
        return "keep_referenced_do_not_rename_now"

    if any(low.startswith(prefix) for prefix in RISK_PREFIXES):
        if refs:
            return "rename_requires_compat_wrapper_and_import_update"
        return "rename_possible_but_runtime_smoke_required"

    if refs:
        return "keep_or_rename_with_reference_update"

    return "manual_review"

def main():
    if not A10F_JSON.exists():
        raise SystemExit("A10F raporu bulunamadı. Önce A10F/A10H zinciri tamamlanmalı.")

    a10f = read_json(A10F_JSON)
    remaining = a10f.get("keep_or_review", [])

    plan = []
    by_decision = {}

    for item in remaining:
        path = item.get("path", "")
        refs = find_references(path)
        decision = classify_remaining(item, refs)
        suggestion = suggested_name(path)

        row = dict(item)
        row["reference_count_now"] = len(refs)
        row["references_now_sample"] = refs[:15]
        row["suggested_new_path"] = suggestion
        row["a10i_decision"] = decision
        row["risk_note"] = (
            "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
            if decision != "manual_review"
            else "Manuel inceleme gerekir."
        )

        plan.append(row)
        by_decision[decision] = by_decision.get(decision, 0) + 1

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10I_REMAINING_RUNTIME_RENAME_KEEP_PLAN",
        "mode": "plan_only",
        "remaining_count": len(remaining),
        "by_decision": by_decision,
        "plan": plan,
        "ok": len(remaining) == 0,
        "next_action": "A10J: yalnızca düşük riskli rename_possible dosyaları için compatibility wrapper planı veya keep allowlist hazırlanmalı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10I Kalan Runtime / Referanslı Dosya Planı",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Özet",
        "",
        f"- Remaining count: {result['remaining_count']}",
        f"- A10I OK: {result['ok']}",
        "",
        "## Karar Dağılımı",
        "",
        "```json",
        json.dumps(result["by_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Plan İlk 200",
        "",
        "```json",
        json.dumps(result["plan"][:200], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Not",
        "",
        "Bu rapor dosya değiştirmez. Kalan dosyalar güvenli karantina adayı değildir; runtime, referans veya uyumluluk riski taşıdığı için ayrı ele alınacaktır.",
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A10I_REPORT_JSON:", OUT_JSON)
    print("A10I_REPORT_MD:", OUT_MD)
    print("A10I_REMAINING_COUNT:", result["remaining_count"])
    print("A10I_BY_DECISION:", json.dumps(result["by_decision"], ensure_ascii=False))
    print("A10I_OK:", result["ok"])

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
