from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from pathlib import Path


TARGET_REL = "scripts/quality/analyze_p13_b_repair_script_inventory_v1.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def scan_except_without_log(text: str) -> list[dict[str, int | str]]:
    # Quality rule cares about except blocks whose body has no logging/print/raise.
    pattern = re.compile(
        r"(?P<indent>^[ \t]*)except\s+(?P<exc>[^:\n]+):\s*\n(?P<body>(?:(?P=indent)[ \t]+[^\n]*\n?)+)",
        re.MULTILINE,
    )
    findings: list[dict[str, int | str]] = []
    lines = text.splitlines()
    for match in pattern.finditer(text):
        body = match.group("body")
        body_low = body.lower()
        if ("print(" not in body_low and "logging." not in body_low and "logger." not in body_low and "raise" not in body_low):
            line_no = text[:match.start()].count("\n") + 1
            snippet = "\n".join(lines[max(0, line_no - 2): min(len(lines), line_no + 5)])
            findings.append({"line": line_no, "snippet": snippet})
    return findings


def patch_first_simple_except(text: str) -> tuple[str, dict[str, object]]:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    changed = False
    info: dict[str, object] = {
        "changed": False,
        "line": None,
        "old_block": "",
        "new_block": "",
    }

    while i < len(lines):
        line = lines[i]
        next_line = lines[i + 1] if i + 1 < len(lines) else ""

        m = re.match(r"^(?P<indent>[ \t]*)except\s+(?P<exc>[^:\n]+):\s*$", line)
        if not changed and m and re.match(r"^[ \t]*(continue|pass)\s*(?:#.*)?$", next_line):
            indent = m.group("indent")
            exc_expr = m.group("exc").strip()
            body_indent = re.match(r"^(?P<indent>[ \t]*)", next_line).group("indent")
            body_stmt = next_line.strip().split("#", 1)[0].strip()

            if " as " in exc_expr:
                new_except = line
                exc_name = exc_expr.split(" as ", 1)[1].strip() or "exc"
            else:
                new_except = f"{indent}except {exc_expr} as exc:"
                exc_name = "exc"

            new_print = (
                f'{body_indent}print("BYS360_P13_B_REFERENCE_SCAN_WARN '
                f'line={i + 1} error=" + repr({exc_name}))'
            )

            out.append(new_except)
            out.append(new_print)
            if body_stmt == "continue":
                out.append(f"{body_indent}continue")

            changed = True
            info = {
                "changed": True,
                "line": i + 1,
                "old_block": line + "\n" + next_line,
                "new_block": "\n".join(out[-(3 if body_stmt == "continue" else 2):]),
            }
            i += 2
            continue

        out.append(line)
        i += 1

    trailing = "\n" if text.endswith("\n") else ""
    return "\n".join(out) + trailing, info


def apply(project_root: Path, dry_run: bool) -> None:
    print("BYS360_QUALITY_10_10_P13_F_REPAIR_INVENTORY_EXCEPT_LOG_FIX_START")
    print(f"project_root={project_root}")
    print(f"mode={'DRY_RUN' if dry_run else 'APPLY'}")

    target = project_root / TARGET_REL
    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    original = read_text(target)
    before = scan_except_without_log(original)

    updated, change_info = patch_first_simple_except(original)
    after = scan_except_without_log(updated)

    if before and not change_info["changed"]:
        raise SystemExit("EXCEPT_WITHOUT_LOG_FOUND_BUT_NOT_PATCHED")

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"p13_f_repair_inventory_except_log_fix_{stamp}"

    if not dry_run and updated != original:
        backup = backup_root / TARGET_REL
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
        write_text(target, updated)

    report = {
        "mode": "DRY_RUN" if dry_run else "APPLY",
        "target": TARGET_REL,
        "changed": updated != original,
        "before_except_without_log_count": len(before),
        "after_except_without_log_count": len(after),
        "before_findings": before,
        "after_findings": after,
        "change_info": change_info,
        "backup_root": str(backup_root) if (not dry_run and updated != original) else None,
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "dryrun" if dry_run else "applied"
    report_json = out_dir / f"bys360_quality_10_10_p13_f_repair_inventory_except_log_fix_{suffix}_v1.json"
    report_md = out_dir / f"bys360_quality_10_10_p13_f_repair_inventory_except_log_fix_{suffix}_v1.md"
    write_text(report_json, json.dumps(report, ensure_ascii=False, indent=2))

    md = []
    md.append("# BYS360 P13-F Repair Inventory Except Log Fix")
    md.append("")
    md.append(f"- Mod: `{report['mode']}`")
    md.append(f"- Hedef: `{TARGET_REL}`")
    md.append(f"- Değişti: {report['changed']}")
    md.append(f"- Önce except-without-log: {len(before)}")
    md.append(f"- Sonra except-without-log: {len(after)}")
    if report["backup_root"]:
        md.append(f"- Yedek: `{report['backup_root']}`")
    write_text(report_md, "\n".join(md) + "\n")

    print(f"target={TARGET_REL}")
    print(f"changed={updated != original}")
    print(f"before_except_without_log_count={len(before)}")
    print(f"after_except_without_log_count={len(after)}")
    if change_info["changed"]:
        print(f"changed_line={change_info['line']}")
    print(f"repair_inventory_except_log_fix_json={report_json}")
    print(f"repair_inventory_except_log_fix_md={report_md}")
    print("BYS360_QUALITY_10_10_P13_F_REPAIR_INVENTORY_EXCEPT_LOG_FIX_OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    apply(Path(args.project_root).resolve(), args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
