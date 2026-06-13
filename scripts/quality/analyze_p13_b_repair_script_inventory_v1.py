from __future__ import annotations

import argparse
import logging
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any



LOGGER = logging.getLogger(__name__)

SCRIPT_DIRS = [
    "scripts/windows",
    "scripts/quality",
    "scripts/security",
    "app/scripts/windows",
    "app/scripts/quality",
]

SCRIPT_EXTS = {".ps1", ".py", ".bat", ".cmd"}

CURRENT_PHASE_HINTS = [
    "p13",
    "p12",
    "p11",
    "quality_10_10",
    "secure_release",
    "secret_clean",
]

ARCHIVE_NAME_HINTS = [
    "repair_",
    "fix_",
    "hotfix",
    "temp",
    "tmp",
    "old",
    "legacy",
    "backup",
    "b42",
    "b46",
    "b48",
    "b49",
    "b50",
    "b51",
    "b52",
    "v2_8_",
    "ios_pwa_v",
    "mobile_v2_",
]

KEEP_NAME_HINTS = [
    "check_bys360_quality_10_10_p3_clean_audit",
    "analyze_bys360_quality_10_10_p7_findings",
    "analyze_bys360_quality_10_10_p10_2_final_p1_decision",
    "analyze_bys360_quality_10_10_p11_refactor_plan",
    "analyze_bys360_quality_10_10_p13_a_effective_p1_closure_map",
    "analyze_bys360_quality_10_10_p12_b_technical_ui_term_decision",
    "build_bys360_secure_release",
    "check_bys360_secure_release",
]

CONTENT_RISK_HINTS = [
    "Remove-Item",
    "rm ",
    "rmdir",
    "del ",
    "DROP TABLE",
    "db.drop",
    "ALTER TABLE",
    "TRUNCATE",
    "delete(",
    "shutil.rmtree",
    "os.remove",
    "Set-Content",
    "Add-Content",
    "Copy-Item",
    "Move-Item",
    "Expand-Archive",
]

SAFE_ANALYSIS_HINTS = [
    "analyze_",
    "inventory",
    "report",
    "json",
    "md",
    "print(",
    "Write-Host",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def classify_kind(name: str, text: str) -> str:
    low = name.lower()
    if "analyze" in low or "inventory" in low:
        return "analysis_report"
    if "check" in low or "gate" in low:
        return "check_gate"
    if "repair" in low or "fix" in low or "hotfix" in low:
        return "repair_fix"
    if "build" in low or "release" in low:
        return "build_release"
    if "split" in low:
        return "split_packaging"
    if "security" in low or "secret" in low:
        return "security"
    if "migrate" in low or "migration" in low:
        return "migration"
    if "apply" in low:
        return "apply_patch"
    return "other"


def detect_version_group(name: str) -> str:
    low = name.lower()
    m = re.search(r"(p\d+(?:[_-][a-z0-9]+)*)", low)
    if m:
        return m.group(1)
    m = re.search(r"(v\d+(?:[_\.-]\d+){0,4})", low)
    if m:
        return m.group(1)
    m = re.search(r"(b\d+[a-z]?)", low)
    if m:
        return m.group(1)
    return "unversioned"


def count_references(project_root: Path, rel_path: str, max_files: int = 2500) -> int:
    # Lightweight reference scan in project text files, excluding backups/reports and binary dirs.
    needle1 = rel_path.replace("\\", "/")
    needle2 = Path(rel_path).name
    total = 0
    scanned = 0
    exts = {".ps1", ".py", ".md", ".txt", ".html", ".jinja", ".jinja2", ".json", ".yml", ".yaml"}
    excluded_parts = {
        ".git", ".venv", "venv", "__pycache__", ".quality_backup", "_upload_parts",
        "node_modules", "build", "dist", ".dart_tool", "reports"
    }
    for path in project_root.rglob("*"):
        if scanned >= max_files:
            break
        if not path.is_file() or path.suffix.lower() not in exts:
            continue
        rel = path.relative_to(project_root).as_posix()
        if rel == rel_path:
            continue
        if any(part in excluded_parts for part in path.relative_to(project_root).parts):
            continue
        scanned += 1
        try:
            text = read_text(path)
        except Exception as exc:
            logging.warning("BYS360 P13-B script envanteri yardımcı tarama uyarısı: %r", exc)
            continue
        if needle1 in text or needle2 in text:
            total += 1
    return total


def make_script_item(project_root: Path, path: Path) -> dict[str, Any]:
    rel = path.relative_to(project_root).as_posix()
    text = read_text(path)
    name = path.name
    low_name = name.lower()
    low_rel = rel.lower()
    lines = text.splitlines()
    kind = classify_kind(name, text)
    version_group = detect_version_group(name)
    references = count_references(project_root, rel)

    content_risk_hits = [h for h in CONTENT_RISK_HINTS if h.lower() in text.lower()]
    current_phase = any(h in low_name or h in low_rel for h in CURRENT_PHASE_HINTS)
    keep_hint = any(h in low_name for h in KEEP_NAME_HINTS)
    archive_hint = any(h in low_name for h in ARCHIVE_NAME_HINTS)

    if keep_hint or current_phase:
        decision = "KEEP_ACTIVE_QUALITY_CHAIN"
        reason = "Güncel kalite/güvenlik zincirine ait görünüyor."
        risk = "LOW"
    elif kind in {"analysis_report", "check_gate", "security", "build_release"} and references > 0:
        decision = "KEEP_REFERENCED_TOOL"
        reason = "Başka dosyalarda referans var; arşivlenmeden önce elle kontrol edilmeli."
        risk = "LOW_MEDIUM"
    elif kind == "repair_fix" and archive_hint and references == 0:
        decision = "ARCHIVE_CANDIDATE_REPAIR_ARTIFACT"
        reason = "Eski onarım/fix artığı gibi görünüyor ve referans bulunmadı; doğrudan silinmemeli, arşiv adayı."
        risk = "MEDIUM"
    elif kind == "repair_fix":
        decision = "REVIEW_REPAIR_SCRIPT"
        reason = "Onarım scripti; arşivlenmeden önce son kullanım ve bağımlılık kontrolü gerekir."
        risk = "MEDIUM"
    elif kind in {"split_packaging", "apply_patch"} and references == 0:
        decision = "ARCHIVE_CANDIDATE_GENERATION_HELPER"
        reason = "Paketleme/uygulama yardımcısı ve referans bulunmadı; arşiv adayı olabilir."
        risk = "MEDIUM"
    else:
        decision = "REVIEW_KEEP_OR_ARCHIVE"
        reason = "Net karar için manuel kontrol gerekir."
        risk = "MEDIUM"

    destructive = bool(content_risk_hits)
    if destructive and decision.startswith("ARCHIVE_CANDIDATE"):
        # Destructive scripts are often repair scripts; archive may still be right, but mark higher review.
        decision = "REVIEW_DESTRUCTIVE_SCRIPT_BEFORE_ARCHIVE"
        reason = "Dosya silme/taşıma/yazma benzeri komutlar içeriyor; arşivlenmeden önce dikkatli kontrol gerekir."
        risk = "MEDIUM_HIGH"

    stat = path.stat()
    return {
        "path": rel,
        "name": name,
        "suffix": path.suffix.lower(),
        "kind": kind,
        "version_group": version_group,
        "line_count": len(lines),
        "size_bytes": stat.st_size,
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "sha256": file_sha256(path),
        "reference_count": references,
        "content_risk_hits": content_risk_hits,
        "decision": decision,
        "risk": risk,
        "reason": reason,
        "first_line": lines[0].strip() if lines else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=240)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    print("BYS360_QUALITY_10_10_P13_B_REPAIR_SCRIPT_INVENTORY_START")
    print(f"project_root={project_root}")

    scripts: list[dict[str, Any]] = []
    missing_dirs = []

    for rel_dir in SCRIPT_DIRS:
        d = project_root / rel_dir
        if not d.exists():
            missing_dirs.append(rel_dir)
            continue
        for path in sorted(d.rglob("*")):
            if path.is_file() and path.suffix.lower() in SCRIPT_EXTS:
                scripts.append(make_script_item(project_root, path))

    by_kind = Counter(item["kind"] for item in scripts)
    by_decision = Counter(item["decision"] for item in scripts)
    by_risk = Counter(item["risk"] for item in scripts)
    by_dir = Counter(str(Path(item["path"]).parent).replace("\\", "/") for item in scripts)

    archive_candidates = [
        item for item in scripts
        if item["decision"].startswith("ARCHIVE_CANDIDATE")
    ]
    destructive_review = [
        item for item in scripts
        if item["decision"] == "REVIEW_DESTRUCTIVE_SCRIPT_BEFORE_ARCHIVE"
    ]
    keep_items = [
        item for item in scripts
        if item["decision"].startswith("KEEP")
    ]
    review_items = [
        item for item in scripts
        if item["decision"].startswith("REVIEW") and item not in destructive_review
    ]

    archive_plan = {
        "decision": "INVENTORY_ONLY_NO_DELETE",
        "archive_candidates_count": len(archive_candidates),
        "destructive_review_count": len(destructive_review),
        "recommended_next_step": "P13-C archive plan with dry-run move list only; no deletion.",
        "archive_folder_suggestion": "scripts/_archive_quality_repair_YYYYMMDD/",
        "safety_rules": [
            "Script silme yapılmayacak.",
            "Önce arşiv klasörüne taşıma dry-run listesi üretilecek.",
            "Güncel kalite zinciri, güvenlik release scriptleri ve referanslı scriptler tutulacak.",
            "Destructive komut içeren dosyalar ayrı manuel inceleme listesinde kalacak.",
            "Taşıma sonrası compileall ve kalite audit tekrar çalıştırılacak.",
        ],
    }

    result = {
        "script_dirs": SCRIPT_DIRS,
        "missing_dirs": missing_dirs,
        "script_count": len(scripts),
        "by_kind": dict(by_kind.most_common()),
        "by_decision": dict(by_decision.most_common()),
        "by_risk": dict(by_risk.most_common()),
        "by_dir": dict(by_dir.most_common()),
        "keep_items": keep_items,
        "archive_candidates": archive_candidates,
        "destructive_review_items": destructive_review,
        "review_items": review_items,
        "all_scripts": scripts,
        "archive_plan": archive_plan,
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p13_b_repair_script_inventory_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p13_b_repair_script_inventory_v1.md"
    json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P13-B Repair/Check Script Inventory")
    md.append("")
    md.append(f"- Script toplamı: {len(scripts)}")
    md.append(f"- Arşiv adayı: {len(archive_candidates)}")
    md.append(f"- Destructive manuel inceleme: {len(destructive_review)}")
    md.append(f"- Tutulacak aktif zincir: {len(keep_items)}")
    md.append("")
    md.append("## Karar Özeti")
    md.append("")
    for key, count in by_decision.most_common():
        md.append(f"- {key}: {count}")
    md.append("")
    md.append("## Tür Özeti")
    md.append("")
    for key, count in by_kind.most_common():
        md.append(f"- {key}: {count}")
    md.append("")
    md.append("## Arşiv Adayları")
    md.append("")
    if archive_candidates:
        for item in archive_candidates[:200]:
            md.append(f"- `{item['path']}` — {item['kind']} — refs={item['reference_count']} — lines={item['line_count']}")
    else:
        md.append("- Arşiv adayı bulunmadı.")
    md.append("")
    md.append("## Destructive Manuel İnceleme")
    md.append("")
    if destructive_review:
        for item in destructive_review[:200]:
            md.append(f"- `{item['path']}` — hits={', '.join(item['content_risk_hits'])}")
    else:
        md.append("- Destructive manuel inceleme adayı yok.")
    md.append("")
    md.append("## Tutulacak Aktif Zincir")
    md.append("")
    for item in keep_items[:200]:
        md.append(f"- `{item['path']}` — {item['decision']} — refs={item['reference_count']}")
    md.append("")
    md.append("## Güvenlik Kuralları")
    md.append("")
    for item in archive_plan["safety_rules"]:
        md.append(f"- {item}")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"script_count={len(scripts)}")
    print(f"archive_candidates_count={len(archive_candidates)}")
    print(f"destructive_review_count={len(destructive_review)}")
    print(f"keep_active_count={len(keep_items)}")
    print("BYS360_QUALITY_10_10_P13_B_DECISION_SUMMARY")
    for key, count in by_decision.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P13_B_KIND_SUMMARY")
    for key, count in by_kind.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P13_B_ARCHIVE_CANDIDATES")
    for item in archive_candidates[:args.limit]:
        print(f"{item['path']} | kind={item['kind']} | refs={item['reference_count']} | lines={item['line_count']} | risk={item['risk']}")
    print("BYS360_QUALITY_10_10_P13_B_DESTRUCTIVE_REVIEW")
    for item in destructive_review[:args.limit]:
        print(f"{item['path']} | kind={item['kind']} | hits={','.join(item['content_risk_hits'])}")
    print("BYS360_QUALITY_10_10_P13_B_KEEP_ACTIVE")
    for item in keep_items[:args.limit]:
        print(f"{item['path']} | decision={item['decision']} | refs={item['reference_count']} | kind={item['kind']}")
    print(f"repair_script_inventory_json={json_out}")
    print(f"repair_script_inventory_md={md_out}")
    print("BYS360_QUALITY_10_10_P13_B_REPAIR_SCRIPT_INVENTORY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
