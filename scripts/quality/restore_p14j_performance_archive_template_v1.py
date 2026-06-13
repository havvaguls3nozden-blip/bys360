from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError


TARGET_REL = "app/templates/performance/archive/index.html"
TEMPLATE_SOURCE_REL = "app/templates/performance/archive/index.html"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def check_template_syntax(project_root: Path, rel: str) -> None:
    template_root = project_root / "app" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_root)))
    try:
        env.get_template(rel.replace("app/templates/", ""))
    except TemplateSyntaxError as exc:
        raise SystemExit(f"TEMPLATE_SYNTAX_ERROR: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--source-root", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    source_root = Path(args.source_root).resolve() if args.source_root else Path(__file__).resolve().parents[2]
    source_template = source_root / TEMPLATE_SOURCE_REL
    target_template = project_root / TARGET_REL

    print("BYS360_P14J_PERFORMANCE_ARCHIVE_TEMPLATE_RESTORE_START")
    print(f"project_root={project_root}")
    print(f"mode={'DRY_RUN' if args.dry_run else 'APPLY'}")
    print(f"source_template={source_template}")
    print(f"target_template={target_template}")

    if not source_template.exists():
        raise SystemExit(f"SOURCE_TEMPLATE_NOT_FOUND: {source_template}")

    source_text = read_text(source_template)
    changed = True
    already_exists = target_template.exists()
    backup_root = None

    if already_exists:
        current_text = read_text(target_template)
        changed = current_text != source_text
    else:
        current_text = ""

    # Syntax check with temp template root if dry-run/no write.
    tmp_root = project_root / "reports" / "quality" / "_p14j_template_check"
    tmp_template = tmp_root / TARGET_REL
    tmp_template.parent.mkdir(parents=True, exist_ok=True)
    write_text(tmp_template, source_text)
    env = Environment(loader=FileSystemLoader(str(tmp_root / "app" / "templates")))
    try:
        env.get_template("performance/archive/index.html")
        syntax_ok = True
    except TemplateSyntaxError as exc:
        syntax_ok = False
        raise SystemExit(f"TEMPLATE_SYNTAX_ERROR: {exc}")
    finally:
        try:
            shutil.rmtree(tmp_root)
        except Exception:
            pass

    if not args.dry_run and changed:
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root_path = project_root / ".quality_backup" / f"p14j_performance_archive_template_restore_{stamp}"
        if target_template.exists():
            backup = backup_root_path / TARGET_REL
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target_template, backup)
        target_template.parent.mkdir(parents=True, exist_ok=True)
        write_text(target_template, source_text)
        backup_root = str(backup_root_path)

    result = {
        "mode": "DRY_RUN" if args.dry_run else "APPLY",
        "target": TARGET_REL,
        "already_exists": already_exists,
        "changed": changed,
        "syntax_ok": syntax_ok,
        "backup_root": backup_root,
        "note": "Eksik performans arşivi template dosyası geri eklendi; route veya asistan dosyalarına dokunulmadı.",
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "dryrun" if args.dry_run else "applied"
    report_json = out_dir / f"bys360_p14j_performance_archive_template_restore_{suffix}_v1.json"
    report_md = out_dir / f"bys360_p14j_performance_archive_template_restore_{suffix}_v1.md"

    write_text(report_json, json.dumps(result, ensure_ascii=False, indent=2))
    write_text(report_md, "\n".join([
        "# BYS360 P14J Performance Archive Template Restore",
        "",
        f"- Mod: `{result['mode']}`",
        f"- Target: `{TARGET_REL}`",
        f"- Already exists: {already_exists}",
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
    print("BYS360_P14J_PERFORMANCE_ARCHIVE_TEMPLATE_RESTORE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
