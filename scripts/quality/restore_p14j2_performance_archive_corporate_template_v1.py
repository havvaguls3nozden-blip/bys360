from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


TARGET_REL = "app/templates/performance/archive/index.html"
SOURCE_REL = "app/templates/performance/archive/index.html"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def check_template(project_root: Path, rel_template: str) -> None:
    env = Environment(loader=FileSystemLoader(str(project_root / "app" / "templates")))
    env.get_template(rel_template)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--source-root", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    source_root = Path(args.source_root).resolve() if args.source_root else Path(__file__).resolve().parents[2]
    source = source_root / SOURCE_REL
    target = project_root / TARGET_REL

    print("BYS360_P14J2_PERFORMANCE_ARCHIVE_CORPORATE_RESTORE_START")
    print(f"project_root={project_root}")
    print(f"mode={'DRY_RUN' if args.dry_run else 'APPLY'}")
    print(f"source={source}")
    print(f"target={target}")

    if not source.exists():
        raise SystemExit(f"SOURCE_TEMPLATE_NOT_FOUND: {source}")

    source_text = read_text(source)
    already_exists = target.exists()
    current_text = read_text(target) if already_exists else ""
    changed = current_text != source_text

    # Syntax check using temp tree to avoid modifying target in dry-run.
    temp_root = project_root / "reports" / "quality" / "_p14j2_template_check"
    temp_template = temp_root / TARGET_REL
    temp_template.parent.mkdir(parents=True, exist_ok=True)
    write_text(temp_template, source_text)
    try:
        env = Environment(loader=FileSystemLoader(str(temp_root / "app" / "templates")))
        env.get_template("performance/archive/index.html")
        syntax_ok = True
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    backup_root = None
    if not args.dry_run and changed:
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root_path = project_root / ".quality_backup" / f"p14j2_performance_archive_corporate_restore_{stamp}"
        if target.exists():
            backup = backup_root_path / TARGET_REL
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)
        target.parent.mkdir(parents=True, exist_ok=True)
        write_text(target, source_text)
        backup_root = str(backup_root_path)

    result = {
        "mode": "DRY_RUN" if args.dry_run else "APPLY",
        "target": TARGET_REL,
        "already_exists": already_exists,
        "changed": changed,
        "syntax_ok": syntax_ok,
        "backup_root": backup_root,
        "design": "corporate_archive_surface",
        "note": "P14J sade fallback yerine mevcut performans yüzeyleriyle uyumlu Geçmiş Karne Arşivi template'i uygulandı.",
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "dryrun" if args.dry_run else "applied"
    report_json = out_dir / f"bys360_p14j2_performance_archive_corporate_restore_{suffix}_v1.json"
    report_md = out_dir / f"bys360_p14j2_performance_archive_corporate_restore_{suffix}_v1.md"
    write_text(report_json, json.dumps(result, ensure_ascii=False, indent=2))
    write_text(report_md, "\n".join([
        "# BYS360 P14J2 Performance Archive Corporate Restore",
        "",
        f"- Mod: `{result['mode']}`",
        f"- Target: `{TARGET_REL}`",
        f"- Changed: {changed}",
        f"- Syntax OK: {syntax_ok}",
        f"- Backup: `{backup_root}`",
        "",
        result["note"],
        "",
    ]))

    print(f"already_exists={already_exists}")
    print(f"changed={changed}")
    print(f"syntax_ok={syntax_ok}")
    if backup_root:
        print(f"backup_root={backup_root}")
    print(f"report_json={report_json}")
    print(f"report_md={report_md}")
    print("BYS360_P14J2_PERFORMANCE_ARCHIVE_CORPORATE_RESTORE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
