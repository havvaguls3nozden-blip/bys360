from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

KEEP_NAMES = {
    "ruff_score10_b1_summary.json",
    "BYS360_A10R3_CANONICAL_EVIDENCE_MANIFEST.json",
    "BYS360_A10R3_CANONICAL_EVIDENCE_MANIFEST.md",
    "BYS360_A10R2_FINAL_TECH_DEBT_EVIDENCE_CLEAN_ZIP.json",
    "BYS360_A10R2_FINAL_TECH_DEBT_EVIDENCE_CLEAN_ZIP.md",
    "BYS360_A11C_WARNING_ZERO_FINAL_EVIDENCE.json",
    "BYS360_A11C_WARNING_ZERO_FINAL_EVIDENCE.md",
    "BYS360_A12F_UI_TECHNICAL_LANGUAGE_FINAL_EVIDENCE.json",
    "BYS360_A12F_UI_TECHNICAL_LANGUAGE_FINAL_EVIDENCE.md",
    "BYS360_A13A_UI_DESIGN_SYSTEM_INVENTORY.json",
    "BYS360_A13A_UI_DESIGN_SYSTEM_INVENTORY.md",
    "BYS360_A13B_UI_DESIGN_SYSTEM_CONSOLIDATION_PLAN.json",
    "BYS360_A13B_UI_DESIGN_SYSTEM_CONSOLIDATION_PLAN.md",
    "BYS360_SCORE100_FINAL_PASS_92_REPORT.json",
    "BYS360_SCORE100_FINAL_PASS_92_REPORT.md",
}

KEEP_PREFIXES = (
    "BYS360_A10R",
    "BYS360_A11C_WARNING_ZERO_FINAL",
    "BYS360_A12F_UI_TECHNICAL_LANGUAGE_FINAL",
    "BYS360_A13A_UI_DESIGN_SYSTEM_INVENTORY",
    "BYS360_A13B_UI_DESIGN_SYSTEM_CONSOLIDATION_PLAN",
)

ARCHIVE_EXTENSIONS = {".txt", ".log", ".xml", ".csv", ".json", ".md", ".ps1"}

@dataclass
class Candidate:
    rel: str
    size_bytes: int
    sha256: str
    action: str
    reason: str


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_keep(path: Path) -> bool:
    name = path.name
    if name in KEEP_NAMES:
        return True
    return any(name.startswith(prefix) for prefix in KEEP_PREFIXES)


def iter_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted([p for p in root.rglob("*") if p.is_file()], key=lambda p: str(p).lower())


def build_plan(project_root: Path) -> list[Candidate]:
    quality_root = project_root / "reports" / "quality"
    candidates: list[Candidate] = []
    for path in iter_files(quality_root):
        rel = path.relative_to(project_root).as_posix()
        if is_keep(path):
            action = "keep"
            reason = "canonical/recent evidence kept in repo"
        elif path.suffix.lower() in ARCHIVE_EXTENSIONS:
            action = "archive_outside_repo"
            reason = "historical quality evidence; move to external archive"
        else:
            action = "review"
            reason = "unknown extension; manual review"
        candidates.append(
            Candidate(
                rel=rel,
                size_bytes=path.stat().st_size,
                sha256=sha256(path),
                action=action,
                reason=reason,
            )
        )
    return candidates


def write_outputs(plan: list[Candidate], output_root: Path, project_root: Path, archive_root: Path, mode: str) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    data = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "project_root": str(project_root),
        "archive_root": str(archive_root),
        "total_files": len(plan),
        "archive_candidates": sum(1 for c in plan if c.action == "archive_outside_repo"),
        "keep_files": sum(1 for c in plan if c.action == "keep"),
        "review_files": sum(1 for c in plan if c.action == "review"),
        "archive_bytes": sum(c.size_bytes for c in plan if c.action == "archive_outside_repo"),
        "keep_bytes": sum(c.size_bytes for c in plan if c.action == "keep"),
        "files": [asdict(c) for c in plan],
    }
    (output_root / "BYS360_TECH_DEBT_PHASE2A_REPORTS_QUALITY_PLAN.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (output_root / "BYS360_TECH_DEBT_PHASE2A_REPORTS_QUALITY_PLAN.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["action", "reason", "rel", "size_bytes", "sha256"])
        writer.writeheader()
        for item in plan:
            writer.writerow(asdict(item))
    md = []
    md.append("# BYS360 Teknik Borç Faz 2A — reports/quality Arşiv Planı\n")
    md.append(f"Oluşturma zamanı: `{data['generated_at']}`\n")
    md.append(f"Mod: `{mode}`\n")
    md.append("\n## Özet\n")
    md.append("| Ölçüm | Değer |\n|---|---:|\n")
    md.append(f"| Toplam reports/quality dosyası | {data['total_files']} |\n")
    md.append(f"| Dış arşive taşınacak aday | {data['archive_candidates']} |\n")
    md.append(f"| Repoda tutulacak kanıt | {data['keep_files']} |\n")
    md.append(f"| Manuel inceleme | {data['review_files']} |\n")
    md.append(f"| Dış arşive taşınacak boyut | {round(data['archive_bytes'] / 1024 / 1024, 2)} MB |\n")
    md.append(f"| Repoda kalacak boyut | {round(data['keep_bytes'] / 1024 / 1024, 2)} MB |\n")
    md.append("\n## İlke\n")
    md.append("Bu faz uygulama kodunu değiştirmez. Sadece geçmiş kalite kanıtlarını proje kökünden ayırmayı hedefler.\n")
    md.append("Apply modunda dosyalar silinmez; `C:\\bys360\\archive` altında zaman damgalı klasöre taşınır.\n")
    md.append("\n## İlk 80 aday\n")
    md.append("| Aksiyon | Dosya | Boyut KB | Sebep |\n|---|---|---:|---|\n")
    for item in plan[:80]:
        md.append(f"| {item.action} | `{item.rel}` | {round(item.size_bytes / 1024, 1)} | {item.reason} |\n")
    (output_root / "BYS360_TECH_DEBT_PHASE2A_REPORTS_QUALITY_PLAN.md").write_text("".join(md), encoding="utf-8")


def apply_archive(plan: list[Candidate], project_root: Path, archive_root: Path) -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_base = archive_root / f"reports_quality_phase2a_{stamp}"
    dest_base.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, str | int]] = []
    for item in plan:
        if item.action != "archive_outside_repo":
            continue
        src = project_root / item.rel
        if not src.exists():
            continue
        dest = dest_base / item.rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        manifest.append({"rel": item.rel, "size_bytes": item.size_bytes, "sha256": item.sha256, "archived_to": str(dest)})
    (dest_base / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 Phase2A reports/quality archive planner")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--archive-root", default=r"C:\bys360\archive")
    parser.add_argument("--mode", choices=["dry-run", "apply"], default="dry-run")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    output_root = Path(args.output_root).resolve()
    archive_root = Path(args.archive_root).resolve()
    plan = build_plan(project_root)
    write_outputs(plan, output_root, project_root, archive_root, args.mode)
    if args.mode == "apply":
        apply_archive(plan, project_root, archive_root)
        # Re-write final plan after moves for a clear apply evidence file.
        final_plan = build_plan(project_root)
        write_outputs(final_plan, output_root, project_root, archive_root, "apply-final")
    print(f"OK: Phase2A reports/quality plan produced: {output_root}")
    print("OK: Code behavior was not modified.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
