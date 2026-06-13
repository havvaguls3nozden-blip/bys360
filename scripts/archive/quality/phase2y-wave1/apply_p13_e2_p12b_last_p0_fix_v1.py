from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from pathlib import Path


TARGET_REL = "scripts/quality/analyze_p12_b_technical_ui_term_decision_v1.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def scan_silent_except_pass(text: str) -> list[dict[str, int | str]]:
    pattern = re.compile(
        r"(?P<indent>^[ \t]*)except\s+[^:\n]+:\s*\n(?P=indent)[ \t]+pass\s*(?:#.*)?$",
        re.MULTILINE,
    )
    findings: list[dict[str, int | str]] = []
    lines = text.splitlines()
    for match in pattern.finditer(text):
        line_no = text[:match.start()].count("\n") + 1
        snippet = "\n".join(lines[max(0, line_no - 2): min(len(lines), line_no + 3)])
        findings.append({"line": line_no, "snippet": snippet})
    return findings


def replace_first_silent_except_pass(text: str) -> tuple[str, dict[str, object]]:
    lines = text.splitlines()
    changed = False
    change_info: dict[str, object] = {
        "changed": False,
        "line": None,
        "old_block": "",
        "new_block": "",
    }

    out_lines: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        next_line = lines[i + 1] if i + 1 < len(lines) else ""

        match = re.match(r"^(?P<indent>[ \t]*)except\s+(?P<exc>[^:\n]+):\s*$", line)
        if (
            not changed
            and match
            and re.match(r"^[ \t]*pass\s*(?:#.*)?$", next_line)
        ):
            indent = match.group("indent")
            pass_indent = re.match(r"^(?P<indent>[ \t]*)", next_line).group("indent")
            exc_expr = match.group("exc").strip()

            if " as " in exc_expr:
                new_except = line
                exc_name = exc_expr.split(" as ", 1)[1].strip() or "exc"
            else:
                new_except = f"{indent}except {exc_expr} as exc:"
                exc_name = "exc"

            new_warn = (
                f'{pass_indent}print("BYS360_P12_B_SUMMARY_COUNT_PARSE_WARN '
                f'line={i + 1} error=" + repr({exc_name}))'
            )

            out_lines.append(new_except)
            out_lines.append(new_warn)

            changed = True
            change_info = {
                "changed": True,
                "line": i + 1,
                "old_block": line + "\n" + next_line,
                "new_block": new_except + "\n" + new_warn,
            }
            i += 2
            continue

        out_lines.append(line)
        i += 1

    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else ""), change_info


def apply(project_root: Path, dry_run: bool) -> None:
    print("BYS360_QUALITY_10_10_P13_E2_P12B_LAST_P0_FIX_START")
    print(f"project_root={project_root}")
    print(f"mode={'DRY_RUN' if dry_run else 'APPLY'}")

    target = project_root / TARGET_REL
    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    original = read_text(target)
    before = scan_silent_except_pass(original)

    updated, change_info = replace_first_silent_except_pass(original)
    after = scan_silent_except_pass(updated)

    if len(before) == 0:
        print("NO_SILENT_EXCEPT_PASS_FOUND_IN_TARGET")
    if len(before) > 0 and not change_info["changed"]:
        raise SystemExit("SILENT_EXCEPT_PASS_FOUND_BUT_NOT_REPLACED")

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"p13_e2_p12b_last_p0_fix_{stamp}"

    if not dry_run and updated != original:
        backup = backup_root / TARGET_REL
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
        write_text(target, updated)

    report = {
        "mode": "DRY_RUN" if dry_run else "APPLY",
        "target": TARGET_REL,
        "changed": updated != original,
        "before_silent_except_pass_count": len(before),
        "after_silent_except_pass_count": len(after),
        "before_findings": before,
        "after_findings": after,
        "change_info": change_info,
        "backup_root": str(backup_root) if (not dry_run and updated != original) else None,
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "dryrun" if dry_run else "applied"
    report_json = out_dir / f"bys360_quality_10_10_p13_e2_p12b_last_p0_fix_{suffix}_v1.json"
    report_md = out_dir / f"bys360_quality_10_10_p13_e2_p12b_last_p0_fix_{suffix}_v1.md"

    write_text(report_json, json.dumps(report, ensure_ascii=False, indent=2))

    md = []
    md.append("# BYS360 P13-E2 P12-B Last P0 Fix")
    md.append("")
    md.append(f"- Mod: `{report['mode']}`")
    md.append(f"- Hedef: `{TARGET_REL}`")
    md.append(f"- Değişti: {report['changed']}")
    md.append(f"- Önce silent except/pass: {len(before)}")
    md.append(f"- Sonra silent except/pass: {len(after)}")
    if report["backup_root"]:
        md.append(f"- Yedek: `{report['backup_root']}`")
    report_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"target={TARGET_REL}")
    print(f"changed={updated != original}")
    print(f"before_silent_except_pass_count={len(before)}")
    print(f"after_silent_except_pass_count={len(after)}")
    if change_info["changed"]:
        print(f"changed_line={change_info['line']}")
    print(f"p12b_last_p0_fix_report_json={report_json}")
    print(f"p12b_last_p0_fix_report_md={report_md}")
    print("BYS360_QUALITY_10_10_P13_E2_P12B_LAST_P0_FIX_OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    apply(Path(args.project_root).resolve(), args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
