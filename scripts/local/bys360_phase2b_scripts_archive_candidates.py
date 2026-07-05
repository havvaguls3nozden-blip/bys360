from __future__ import annotations

import argparse
import csv
import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class PlanItem:
    action: str
    rel: str
    destination: str
    reason: str
    size_kb: float


def read_inventory(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Inventory CSV bulunamadı: {csv_path}")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_plan(project_root: Path, output_root: Path, archive_root: Path) -> tuple[list[PlanItem], list[str]]:
    inventory_csv = output_root / "BYS360_TECH_DEBT_PHASE2B_SCRIPTS_INVENTORY.csv"
    rows = read_inventory(inventory_csv)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination_root = archive_root / f"scripts_phase2b_archive_candidates_{timestamp}"
    plan: list[PlanItem] = []
    warnings: list[str] = []

    for row in rows:
        action = (row.get("action") or "").strip()
        rel = (row.get("rel") or row.get("file") or "").strip().replace("/", "\\")
        if action != "archive_candidate":
            continue
        if not rel.lower().startswith("scripts\\"):
            warnings.append(f"SKIP non-scripts path: {rel}")
            continue
        src = project_root / rel
        if not src.exists() or not src.is_file():
            warnings.append(f"SKIP missing file: {rel}")
            continue
        dest = destination_root / rel
        size_kb = round(src.stat().st_size / 1024, 2)
        reason = row.get("reason") or row.get("priority_reason") or "archive_candidate from phase2b inventory"
        plan.append(PlanItem("archive_outside_repo", rel.replace("\\", "/"), str(dest), reason, size_kb))

    return plan, warnings


def write_reports(output_root: Path, mode: str, plan: list[PlanItem], warnings: list[str], archive_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    total_kb = round(sum(item.size_kb for item in plan), 2)
    md = output_root / "BYS360_TECH_DEBT_PHASE2B_ARCHIVE_CANDIDATES_PLAN.md"
    js = output_root / "BYS360_TECH_DEBT_PHASE2B_ARCHIVE_CANDIDATES_PLAN.json"
    csvp = output_root / "BYS360_TECH_DEBT_PHASE2B_ARCHIVE_CANDIDATES_PLAN.csv"

    lines = [
        "# BYS360 Teknik Borç Faz 2B — Script Arşiv Adayları Planı",
        f"Oluşturma zamanı: `{datetime.now().isoformat(timespec='seconds')}`",
        f"Mod: `{mode}`",
        "",
        "## Özet",
        "| Ölçüm | Değer |",
        "|---|---:|",
        f"| Arşiv adayı script | {len(plan)} |",
        f"| Toplam boyut | {total_kb} KB |",
        f"| Uyarı | {len(warnings)} |",
        f"| Dış arşiv kökü | `{archive_root}` |",
        "",
        "## İlke",
        "Bu faz uygulama kodunu değiştirmez. Sadece Phase 2B envanterinde `archive_candidate` olarak sınıflanan tek seferlik scriptleri repo dışı arşive taşımayı planlar.",
        "`review` ve `tooling_keep` sınıfındaki scriptlere dokunulmaz.",
        "Apply modunda dosyalar silinmez; `C:\\bys360\\archive` altında zaman damgalı klasöre taşınır.",
        "",
        "## İlk 120 Aday",
        "| Aksiyon | Dosya | Boyut KB | Sebep |",
        "|---|---|---:|---|",
    ]
    for item in plan[:120]:
        lines.append(f"| {item.action} | `{item.rel}` | {item.size_kb} | {item.reason} |")
    if warnings:
        lines += ["", "## Uyarılar"]
        lines += [f"- {w}" for w in warnings[:200]]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    js.write_text(json.dumps({"mode": mode, "archive_root": str(archive_root), "count": len(plan), "total_kb": total_kb, "warnings": warnings, "items": [asdict(p) for p in plan]}, ensure_ascii=False, indent=2), encoding="utf-8")

    with csvp.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["action", "rel", "destination", "reason", "size_kb"])
        writer.writeheader()
        for item in plan:
            writer.writerow(asdict(item))


def apply_plan(project_root: Path, plan: list[PlanItem]) -> None:
    for item in plan:
        src = project_root / item.rel
        dest = Path(item.destination)
        if not src.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 Phase2B scripts archive candidates")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["dry-run", "apply"], default="dry-run")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--archive-root", default=r"C:\bys360\archive")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    output_root = Path(args.output_root).resolve()
    archive_root = Path(args.archive_root).resolve()
    plan, warnings = build_plan(project_root, output_root, archive_root)
    write_reports(output_root, args.mode, plan, warnings, archive_root)
    if args.mode == "apply":
        apply_plan(project_root, plan)
    print(f"OK: Phase2B script archive candidates plan produced: {output_root}")
    print(f"OK: archive_candidate count: {len(plan)}")
    if warnings:
        print(f"WARN: {len(warnings)} uyarı var; plan raporuna bakın.")
    if args.mode == "dry-run":
        print("OK: Dry-run modunda dosya taşınmadı.")
    else:
        print("OK: Apply modunda archive_candidate scriptler dış arşive taşındı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
