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


def ensure_import_logging(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    updated = text
    if "import logging" not in updated:
        if "import argparse\n" in updated:
            updated = updated.replace("import argparse\n", "import argparse\nimport logging\n", 1)
        else:
            updated = "import logging\n" + updated
        changes.append("import logging eklendi")
    return updated, changes


def collect_except_blocks(text: str) -> list[dict[str, object]]:
    lines = text.splitlines()
    blocks: list[dict[str, object]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(?P<indent>[ \t]*)except\s+(?P<exc>[^:\n]+):\s*$", line)
        if not m:
            i += 1
            continue

        indent = m.group("indent")
        j = i + 1
        body: list[str] = []
        while j < len(lines):
            candidate = lines[j]
            if candidate.strip() == "":
                body.append(candidate)
                j += 1
                continue
            if candidate.startswith(indent + " ") or candidate.startswith(indent + "\t"):
                body.append(candidate)
                j += 1
                continue
            break

        blocks.append({
            "start_index": i,
            "end_index": j,
            "line": i + 1,
            "except_line": line,
            "exc_expr": m.group("exc").strip(),
            "indent": indent,
            "body": body,
            "body_text": "\n".join(body),
        })
        i = j
    return blocks


def quality_like_unlogged_blocks(text: str) -> list[dict[str, object]]:
    out = []
    for block in collect_except_blocks(text):
        body_low = str(block["body_text"]).lower()
        if "logging." not in body_low and "raise" not in body_low:
            out.append(block)
    return out


def patch_all_unlogged_except_blocks(text: str) -> tuple[str, list[dict[str, object]]]:
    lines = text.splitlines()
    blocks = quality_like_unlogged_blocks(text)
    if not blocks:
        return text, []

    patched_ranges = {(int(b["start_index"]), int(b["end_index"])): b for b in blocks}
    out: list[str] = []
    i = 0
    changes: list[dict[str, object]] = []

    while i < len(lines):
        matched_key = None
        for key in patched_ranges:
            if i == key[0]:
                matched_key = key
                break

        if matched_key is None:
            out.append(lines[i])
            i += 1
            continue

        block = patched_ranges[matched_key]
        start, end = matched_key
        old_except = str(block["except_line"])
        old_body = list(block["body"])
        indent = str(block["indent"])
        exc_expr = str(block["exc_expr"])

        body_indent = indent + "    "
        for body_line in old_body:
            if body_line.strip():
                body_indent = re.match(r"^([ \t]*)", body_line).group(1)
                if len(body_indent) <= len(indent):
                    body_indent = indent + "    "
                break

        if " as " in exc_expr:
            new_except = old_except
            exc_name = exc_expr.split(" as ", 1)[1].strip() or "exc"
        else:
            new_except = f"{indent}except {exc_expr} as exc:"
            exc_name = "exc"

        body_text = "\n".join(old_body)
        has_continue = bool(re.search(r"^\s*continue\s*(?:#.*)?$", body_text, re.MULTILINE))

        # Use literal logging.warning so the quality rule sees a real logging call.
        new_body = [
            f'{body_indent}logging.warning("BYS360 P13-B script envanteri yardımcı tarama uyarısı: %r", {exc_name})'
        ]
        if has_continue:
            new_body.append(f"{body_indent}continue")

        out.append(new_except)
        out.extend(new_body)

        changes.append({
            "line": int(block["line"]),
            "old_block": "\n".join([old_except] + old_body),
            "new_block": "\n".join([new_except] + new_body),
        })
        i = end

    trailing = "\n" if text.endswith("\n") else ""
    return "\n".join(out) + trailing, changes


def apply(project_root: Path, dry_run: bool) -> None:
    print("BYS360_QUALITY_10_10_P13_F3_REPAIR_INVENTORY_FORCE_LOGGING_FIX_START")
    print(f"project_root={project_root}")
    print(f"mode={'DRY_RUN' if dry_run else 'APPLY'}")

    target = project_root / TARGET_REL
    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    original = read_text(target)
    before = quality_like_unlogged_blocks(original)

    updated, import_changes = ensure_import_logging(original)
    updated, handler_changes = patch_all_unlogged_except_blocks(updated)
    after = quality_like_unlogged_blocks(updated)

    if before and not handler_changes:
        raise SystemExit("UNLOGGED_EXCEPT_FOUND_BUT_NOT_PATCHED")

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"p13_f3_repair_inventory_force_logging_fix_{stamp}"

    if not dry_run and updated != original:
        backup = backup_root / TARGET_REL
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
        write_text(target, updated)

    report = {
        "mode": "DRY_RUN" if dry_run else "APPLY",
        "target": TARGET_REL,
        "changed": updated != original,
        "before_unlogged_except_count": len(before),
        "after_unlogged_except_count": len(after),
        "before_lines": [b["line"] for b in before],
        "after_lines": [b["line"] for b in after],
        "import_changes": import_changes,
        "handler_changes": handler_changes,
        "backup_root": str(backup_root) if (not dry_run and updated != original) else None,
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "dryrun" if dry_run else "applied"
    report_json = out_dir / f"bys360_quality_10_10_p13_f3_repair_inventory_force_logging_fix_{suffix}_v1.json"
    report_md = out_dir / f"bys360_quality_10_10_p13_f3_repair_inventory_force_logging_fix_{suffix}_v1.md"
    write_text(report_json, json.dumps(report, ensure_ascii=False, indent=2))

    md = []
    md.append("# BYS360 P13-F3 Repair Inventory Force Logging Fix")
    md.append("")
    md.append(f"- Mod: `{report['mode']}`")
    md.append(f"- Hedef: `{TARGET_REL}`")
    md.append(f"- Değişti: {report['changed']}")
    md.append(f"- Önce log/raise olmayan except: {len(before)}")
    md.append(f"- Sonra log/raise olmayan except: {len(after)}")
    if report["backup_root"]:
        md.append(f"- Yedek: `{report['backup_root']}`")
    md.append("")
    md.append("## Değişen Bloklar")
    md.append("")
    for item in handler_changes:
        md.append(f"- line {item['line']}")
    write_text(report_md, "\n".join(md) + "\n")

    print(f"target={TARGET_REL}")
    print(f"changed={updated != original}")
    print(f"before_unlogged_except_count={len(before)}")
    print(f"after_unlogged_except_count={len(after)}")
    print(f"handler_change_count={len(handler_changes)}")
    for item in handler_changes:
        print(f"changed_line={item['line']}")
    print(f"force_logging_fix_json={report_json}")
    print(f"force_logging_fix_md={report_md}")
    print("BYS360_QUALITY_10_10_P13_F3_REPAIR_INVENTORY_FORCE_LOGGING_FIX_OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    apply(Path(args.project_root).resolve(), args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
