from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


P13_B_REL = "reports/quality/bys360_quality_10_10_p13_b_repair_script_inventory_v1.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def safe_rel_path(value: str) -> str:
    rel = str(value or "").replace("\\", "/").strip()
    if not rel or rel.startswith("/") or ".." in Path(rel).parts:
        raise ValueError(f"UNSAFE_RELATIVE_PATH: {value}")
    return rel


def build_move_plan(project_root: Path, archive_date: str) -> dict[str, Any]:
    p13_b_path = project_root / P13_B_REL
    if not p13_b_path.exists():
        raise SystemExit(f"P13_B_REPORT_NOT_FOUND: {p13_b_path}")

    p13_b = load_json(p13_b_path)
    archive_candidates = list(p13_b.get("archive_candidates") or [])
    destructive_review_items = list(p13_b.get("destructive_review_items") or [])
    keep_items = list(p13_b.get("keep_items") or [])
    review_items = list(p13_b.get("review_items") or [])

    archive_root = f"scripts/_archive_quality_repair_{archive_date}"

    moves = []
    blocked = []

    for item in archive_candidates:
        rel = safe_rel_path(item.get("path"))
        source = project_root / rel
        if not source.exists():
            blocked.append({
                "path": rel,
                "reason": "SOURCE_NOT_FOUND",
                "decision": item.get("decision"),
            })
            continue

        # Preserve subfolder under archive root.
        destination_rel = f"{archive_root}/{rel}"
        moves.append({
            "source": rel,
            "destination": destination_rel,
            "reason": item.get("reason"),
            "decision": item.get("decision"),
            "kind": item.get("kind"),
            "reference_count": item.get("reference_count"),
            "line_count": item.get("line_count"),
            "sha256": item.get("sha256"),
        })

    for item in destructive_review_items:
        blocked.append({
            "path": item.get("path"),
            "reason": "DESTRUCTIVE_REVIEW_NOT_ARCHIVED",
            "decision": item.get("decision"),
            "content_risk_hits": item.get("content_risk_hits"),
        })

    # A PowerShell script text for the future, intentionally marked as dry-run only.
    dryrun_ps_lines = [
        "# P13-C dry-run archive plan only. This script does not move files.",
        "$ProjectRoot = \"C:\\bys360\\project\"",
        f"$ArchiveRoot = Join-Path $ProjectRoot \"{archive_root}\"",
        "Write-Host \"P13-C dry-run archive plan\"",
        "Write-Host \"ArchiveRoot=$ArchiveRoot\"",
    ]
    for move in moves:
        dryrun_ps_lines.append(f"Write-Host \"WOULD_MOVE: {move['source']} -> {move['destination']}\"")

    return {
        "source_report": P13_B_REL,
        "archive_root": archive_root,
        "mode": "DRY_RUN_ONLY_NO_MOVE_NO_DELETE",
        "move_count": len(moves),
        "blocked_count": len(blocked),
        "keep_count": len(keep_items),
        "review_count": len(review_items),
        "moves": moves,
        "blocked_items": blocked,
        "dryrun_powershell_preview": "\n".join(dryrun_ps_lines) + "\n",
        "next_step": "P13-D can generate an apply script only after the dry-run list is approved and a full project checkpoint is taken.",
        "safety_rules": [
            "P13-C hiçbir dosyayı taşımaz veya silmez.",
            "Sadece P13-B tarafından ARCHIVE_CANDIDATE_* olarak işaretlenen ve varlığı doğrulanan dosyalar planlanır.",
            "REVIEW_DESTRUCTIVE_SCRIPT_BEFORE_ARCHIVE dosyaları arşiv planına alınmaz.",
            "KEEP_ACTIVE_QUALITY_CHAIN ve KEEP_REFERENCED_TOOL dosyalarına dokunulmaz.",
            "P13-D yapılırsa önce full checkpoint, sonra dry-run, sonra yalnızca Move-Item ile arşiv klasörüne taşıma; silme yok.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--archive-date", default=dt.datetime.now().strftime("%Y%m%d"))
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    print("BYS360_QUALITY_10_10_P13_C_REPAIR_SCRIPT_ARCHIVE_DRYRUN_START")
    print(f"project_root={project_root}")

    plan = build_move_plan(project_root, args.archive_date)

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p13_c_repair_script_archive_dryrun_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p13_c_repair_script_archive_dryrun_v1.md"
    ps_preview_out = out_dir / "bys360_quality_10_10_p13_c_repair_script_archive_dryrun_preview.ps1"

    json_out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    ps_preview_out.write_text(plan["dryrun_powershell_preview"], encoding="utf-8")

    md = []
    md.append("# BYS360 P13-C Repair Script Archive Dry-Run")
    md.append("")
    md.append(f"- Mod: `{plan['mode']}`")
    md.append(f"- Arşiv kökü: `{plan['archive_root']}`")
    md.append(f"- Taşıma adayı: {plan['move_count']}")
    md.append(f"- Bloke/elle inceleme: {plan['blocked_count']}")
    md.append("")
    md.append("## Taşıma Planı")
    md.append("")
    if plan["moves"]:
        for item in plan["moves"]:
            md.append(f"- `{item['source']}` → `{item['destination']}`")
    else:
        md.append("- Taşıma adayı yok.")
    md.append("")
    md.append("## Arşivlenmeyecek / Bloke")
    md.append("")
    if plan["blocked_items"]:
        for item in plan["blocked_items"]:
            md.append(f"- `{item['path']}` — {item['reason']}")
    else:
        md.append("- Bloke öğe yok.")
    md.append("")
    md.append("## Güvenlik Kuralları")
    md.append("")
    for rule in plan["safety_rules"]:
        md.append(f"- {rule}")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"mode={plan['mode']}")
    print(f"archive_root={plan['archive_root']}")
    print(f"move_count={plan['move_count']}")
    print(f"blocked_count={plan['blocked_count']}")
    print("BYS360_QUALITY_10_10_P13_C_WOULD_MOVE")
    for item in plan["moves"]:
        print(f"{item['source']} -> {item['destination']}")
    print("BYS360_QUALITY_10_10_P13_C_BLOCKED_ITEMS")
    for item in plan["blocked_items"]:
        print(f"{item['path']} | reason={item['reason']}")
    print(f"archive_dryrun_json={json_out}")
    print(f"archive_dryrun_md={md_out}")
    print(f"archive_dryrun_preview_ps1={ps_preview_out}")
    print("BYS360_QUALITY_10_10_P13_C_REPAIR_SCRIPT_ARCHIVE_DRYRUN_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
