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


def ensure_logging(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    updated = text

    if "import logging" not in updated:
        # Put logging near other imports.
        if "import argparse\n" in updated:
            updated = updated.replace("import argparse\n", "import argparse\nimport logging\n", 1)
            changes.append("import logging eklendi")
        else:
            updated = "import logging\n" + updated
            changes.append("import logging dosya başına eklendi")

    if "LOGGER = logging.getLogger(__name__)" not in updated:
        # Place logger after imports block, preferably before constants.
        marker = "\nSCRIPT_DIRS = ["
        if marker in updated:
            updated = updated.replace(marker, "\n\nLOGGER = logging.getLogger(__name__)\n" + marker, 1)
            changes.append("LOGGER sabiti SCRIPT_DIRS öncesine eklendi")
        else:
            updated = updated.replace("import logging\n", "import logging\n\nLOGGER = logging.getLogger(__name__)\n", 1)
            changes.append("LOGGER sabiti import sonrası eklendi")

    return updated, changes


def scan_except_without_logger(text: str) -> list[dict[str, int | str]]:
    pattern = re.compile(
        r"(?P<indent>^[ \t]*)except\s+(?P<exc>[^:\n]+):\s*\n(?P<body>(?:(?P=indent)[ \t]+[^\n]*\n?)+)",
        re.MULTILINE,
    )
    findings: list[dict[str, int | str]] = []
    lines = text.splitlines()
    for match in pattern.finditer(text):
        body = match.group("body")
        body_low = body.lower()
        if (
            "logger." not in body_low
            and "logging." not in body_low
            and "raise" not in body_low
        ):
            line_no = text[:match.start()].count("\n") + 1
            snippet = "\n".join(lines[max(0, line_no - 2): min(len(lines), line_no + 7)])
            findings.append({"line": line_no, "snippet": snippet})
    return findings


def patch_except_blocks(text: str) -> tuple[str, list[dict[str, object]]]:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    changes: list[dict[str, object]] = []

    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(?P<indent>[ \t]*)except\s+(?P<exc>[^:\n]+):\s*$", line)
        if not m:
            out.append(line)
            i += 1
            continue

        indent = m.group("indent")
        exc_expr = m.group("exc").strip()
        j = i + 1
        body_lines: list[str] = []
        while j < len(lines):
            next_line = lines[j]
            if next_line.strip() == "":
                body_lines.append(next_line)
                j += 1
                continue
            if next_line.startswith(indent + " ") or next_line.startswith(indent + "\t"):
                body_lines.append(next_line)
                j += 1
                continue
            break

        body_text = "\n".join(body_lines)
        body_low = body_text.lower()

        if "logger." in body_low or "logging." in body_low or "raise" in body_low:
            out.append(line)
            out.extend(body_lines)
            i = j
            continue

        # Patch only simple silent/print-style handlers. Preserve continue/pass behavior.
        simple_handler = (
            re.search(r"^\s*(pass|continue)\s*(?:#.*)?$", body_text, re.MULTILINE)
            or "BYS360_P13_B_REFERENCE_SCAN_WARN" in body_text
            or "print(" in body_text
        )
        if not simple_handler:
            out.append(line)
            out.extend(body_lines)
            i = j
            continue

        # Ensure exception variable exists.
        if " as " in exc_expr:
            new_except = line
            exc_name = exc_expr.split(" as ", 1)[1].strip() or "exc"
        else:
            new_except = f"{indent}except {exc_expr} as exc:"
            exc_name = "exc"

        body_indent_match = re.match(r"^([ \t]*)", body_lines[0] if body_lines else indent + "    ")
        body_indent = body_indent_match.group(1) if body_indent_match else indent + "    "
        if len(body_indent) <= len(indent):
            body_indent = indent + "    "

        has_continue = bool(re.search(r"^\s*continue\s*(?:#.*)?$", body_text, re.MULTILINE))
        has_pass = bool(re.search(r"^\s*pass\s*(?:#.*)?$", body_text, re.MULTILINE))

        new_body = [
            f'{body_indent}LOGGER.warning("BYS360 P13-B referans tarama uyarısı: %r", {exc_name})'
        ]
        if has_continue:
            new_body.append(f"{body_indent}continue")
        elif has_pass:
            # Do not put pass after logger; logger itself is a body.
            pass
        else:
            # Default: keep flow safe for scanning loops.
            new_body.append(f"{body_indent}continue")

        out.append(new_except)
        out.extend(new_body)

        changes.append({
            "line": i + 1,
            "old_block": line + "\n" + body_text,
            "new_block": "\n".join([new_except] + new_body),
        })
        i = j

    trailing = "\n" if text.endswith("\n") else ""
    return "\n".join(out) + trailing, changes


def apply(project_root: Path, dry_run: bool) -> None:
    print("BYS360_QUALITY_10_10_P13_F2_REPAIR_INVENTORY_LOGGER_FIX_START")
    print(f"project_root={project_root}")
    print(f"mode={'DRY_RUN' if dry_run else 'APPLY'}")

    target = project_root / TARGET_REL
    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    original = read_text(target)
    before = scan_except_without_logger(original)

    updated, logging_changes = ensure_logging(original)
    updated, handler_changes = patch_except_blocks(updated)
    after = scan_except_without_logger(updated)

    if before and not handler_changes:
        raise SystemExit("EXCEPT_WITHOUT_LOG_FOUND_BUT_NOT_PATCHED")

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"p13_f2_repair_inventory_logger_fix_{stamp}"

    if not dry_run and updated != original:
        backup = backup_root / TARGET_REL
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
        write_text(target, updated)

    report = {
        "mode": "DRY_RUN" if dry_run else "APPLY",
        "target": TARGET_REL,
        "changed": updated != original,
        "before_except_without_logger_count": len(before),
        "after_except_without_logger_count": len(after),
        "before_findings": before,
        "after_findings": after,
        "logging_changes": logging_changes,
        "handler_changes": handler_changes,
        "backup_root": str(backup_root) if (not dry_run and updated != original) else None,
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "dryrun" if dry_run else "applied"
    report_json = out_dir / f"bys360_quality_10_10_p13_f2_repair_inventory_logger_fix_{suffix}_v1.json"
    report_md = out_dir / f"bys360_quality_10_10_p13_f2_repair_inventory_logger_fix_{suffix}_v1.md"

    write_text(report_json, json.dumps(report, ensure_ascii=False, indent=2))

    md = []
    md.append("# BYS360 P13-F2 Repair Inventory Logger Fix")
    md.append("")
    md.append(f"- Mod: `{report['mode']}`")
    md.append(f"- Hedef: `{TARGET_REL}`")
    md.append(f"- Değişti: {report['changed']}")
    md.append(f"- Önce except-without-logger: {len(before)}")
    md.append(f"- Sonra except-without-logger: {len(after)}")
    if report["backup_root"]:
        md.append(f"- Yedek: `{report['backup_root']}`")
    md.append("")
    md.append("## Handler Değişiklikleri")
    md.append("")
    for item in handler_changes:
        md.append(f"- line {item['line']}")
    write_text(report_md, "\n".join(md) + "\n")

    print(f"target={TARGET_REL}")
    print(f"changed={updated != original}")
    print(f"before_except_without_logger_count={len(before)}")
    print(f"after_except_without_logger_count={len(after)}")
    print(f"handler_change_count={len(handler_changes)}")
    for item in handler_changes:
        print(f"changed_line={item['line']}")
    print(f"repair_inventory_logger_fix_json={report_json}")
    print(f"repair_inventory_logger_fix_md={report_md}")
    print("BYS360_QUALITY_10_10_P13_F2_REPAIR_INVENTORY_LOGGER_FIX_OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    apply(Path(args.project_root).resolve(), args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
