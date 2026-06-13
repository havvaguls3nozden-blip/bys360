from __future__ import annotations

import logging

import argparse
import datetime as dt
import json
import re
import shutil
import py_compile
from pathlib import Path

# BYS360_A5_P2D5_TOP_LEVEL_LOGGER_ANCHOR
LOGGER = logging.getLogger(__name__)


TARGETS = [
    {
        "path": "app/services/performance/period_delete_service.py",
        "expected_line": 212,
        "label": "period_delete_service",
    },
    {
        "path": "scripts/quality/apply_p14f1_mobile_api_blueprint_name_fix_v1.py",
        "expected_line": 82,
        "label": "p14f1_mobile_blueprint_fix",
    },
    {
        "path": "scripts/quality/apply_p14f2_mobile_api_route_registrar_adapter_v1.py",
        "expected_line": 179,
        "label": "p14f2_mobile_registrar_adapter",
    },
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def ensure_logging_and_logger(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    updated = text

    if "import logging" not in updated:
        import_lines = list(re.finditer(r"^import\s+[A-Za-z0-9_., ]+|^from\s+[A-Za-z0-9_.]+\s+import\s+", updated, flags=re.MULTILINE))
        if import_lines:
            last = import_lines[-1]
            insert_at = updated.find("\n", last.end())
            if insert_at >= 0:
                updated = updated[:insert_at + 1] + "import logging\n" + updated[insert_at + 1:]
            else:
                updated += "\nimport logging\n"
        else:
            updated = "import logging\n" + updated
        changes.append("import logging eklendi")

    if "LOGGER = logging.getLogger(__name__)" not in updated:
        # place after import block
        import_block = list(re.finditer(r"^(?:import\s+.+|from\s+.+\s+import\s+.+)$", updated, flags=re.MULTILINE))
        if import_block:
            last = import_block[-1]
            insert_at = updated.find("\n", last.end())
            if insert_at >= 0:
                updated = updated[:insert_at + 1] + "\nLOGGER = logging.getLogger(__name__)\n" + updated[insert_at + 1:]
            else:
                updated += "\n\nLOGGER = logging.getLogger(__name__)\n"
        else:
            updated = "LOGGER = logging.getLogger(__name__)\n" + updated
        changes.append("LOGGER eklendi")

    return updated, changes


def line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def find_except_blocks(text: str) -> list[dict]:
    lines = text.splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(?P<indent>[ \t]*)except(?P<expr>[^:\n]*):\s*(?P<trailing>#.*)?$", line)
        if not m:
            i += 1
            continue

        indent = m.group("indent")
        j = i + 1
        body = []
        while j < len(lines):
            ln = lines[j]
            if ln.strip() == "":
                body.append(ln)
                j += 1
                continue
            if ln.startswith(indent + " ") or ln.startswith(indent + "\t"):
                body.append(ln)
                j += 1
                continue
            break

        blocks.append({
            "start_index": i,
            "end_index": j,
            "line": i + 1,
            "except_line": line,
            "expr": (m.group("expr") or "").strip(),
            "indent": indent,
            "body": body,
            "body_text": "\n".join(body),
        })
        i = j

    return blocks


def body_is_silent_pass(body_text: str) -> bool:
    useful = []
    for ln in body_text.splitlines():
        stripped = ln.strip()
        if not stripped or stripped.startswith("#"):
            continue
        useful.append(stripped)
    return useful == ["pass"]


def patch_silent_pass_blocks(text: str, label: str) -> tuple[str, list[dict]]:
    lines = text.splitlines()
    blocks = find_except_blocks(text)
    to_patch = [b for b in blocks if body_is_silent_pass(b["body_text"])]

    if not to_patch:
        return text, []

    ranges = {(b["start_index"], b["end_index"]): b for b in to_patch}
    new_lines: list[str] = []
    i = 0
    changes: list[dict] = []

    while i < len(lines):
        key = None
        for r in ranges:
            if i == r[0]:
                key = r
                break

        if key is None:
            new_lines.append(lines[i])
            i += 1
            continue

        block = ranges[key]
        indent = block["indent"]
        expr = block["expr"]
        old_except_line = block["except_line"]
        body = block["body"]

        body_indent = indent + "    "
        for body_line in body:
            if body_line.strip():
                body_indent = re.match(r"^([ \t]*)", body_line).group(1)
                if len(body_indent) <= len(indent):
                    body_indent = indent + "    "
                break

        if expr == "":
            new_except_line = f"{indent}except Exception as exc:"
            exc_name = "exc"
        elif " as " in expr:
            new_except_line = old_except_line
            exc_name = expr.split(" as ", 1)[1].strip() or "exc"
        else:
            new_except_line = f"{indent}except {expr} as exc:"
            exc_name = "exc"

        log_line = (
            f'{body_indent}LOGGER.warning("BYS360 {label} yardımcı işleminde bastırılan hata loglandı: %r", {exc_name})'
        )

        new_lines.append(new_except_line)
        new_lines.append(log_line)

        changes.append({
            "line": block["line"],
            "old_except_line": old_except_line,
            "new_except_line": new_except_line,
            "old_body": block["body_text"],
            "new_body": log_line,
        })
        i = key[1]

    trailing = "\n" if text.endswith("\n") else ""
    return "\n".join(new_lines) + trailing, changes


def compile_text(project_root: Path, rel_path: str, text: str) -> None:
    tmp = project_root / "reports" / "quality" / f"_p14g_compile_check_{Path(rel_path).name}"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    write_text(tmp, text)
    try:
        py_compile.compile(str(tmp), doraise=True)
    finally:
        try:
            tmp.unlink()
        except Exception as exc:
            LOGGER.warning("BYS360 P14-G self-check temizleme sırasında bastırılan hata loglandı: %r", exc)
def apply(project_root: Path, dry_run: bool) -> dict:
    report = {
        "mode": "DRY_RUN" if dry_run else "APPLY",
        "targets": [],
        "total_silent_pass_blocks_patched": 0,
        "backup_root": None,
    }

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"p14_g_p0_silent_except_fix_{stamp}"

    for target in TARGETS:
        rel = target["path"]
        path = project_root / rel
        if not path.exists():
            raise SystemExit(f"TARGET_NOT_FOUND: {path}")

        original = read_text(path)
        updated, logging_changes = ensure_logging_and_logger(original)
        updated, block_changes = patch_silent_pass_blocks(updated, target["label"])

        if not block_changes:
            # Keep going but mark it. The check command will confirm if P0 remains.
            target_result = {
                "path": rel,
                "changed": updated != original,
                "logging_changes": logging_changes,
                "block_changes": [],
                "note": "silent pass block not found by parser",
            }
        else:
            compile_text(project_root, rel, updated)
            target_result = {
                "path": rel,
                "changed": updated != original,
                "logging_changes": logging_changes,
                "block_changes": block_changes,
                "note": "",
            }

        if not dry_run and updated != original:
            backup = backup_root / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)
            write_text(path, updated)

        report["targets"].append(target_result)
        report["total_silent_pass_blocks_patched"] += len(block_changes)

    if not dry_run and any(t["changed"] for t in report["targets"]):
        report["backup_root"] = str(backup_root)

    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    print("BYS360_QUALITY_10_10_P14_G_P0_SILENT_EXCEPT_FIX_START")
    print(f"project_root={project_root}")
    print(f"mode={'DRY_RUN' if args.dry_run else 'APPLY'}")

    result = apply(project_root, dry_run=args.dry_run)

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "dryrun" if args.dry_run else "applied"
    report_json = out_dir / f"bys360_quality_10_10_p14_g_p0_silent_except_fix_{suffix}_v1.json"
    report_md = out_dir / f"bys360_quality_10_10_p14_g_p0_silent_except_fix_{suffix}_v1.md"

    write_text(report_json, json.dumps(result, ensure_ascii=False, indent=2))

    md = [
        "# BYS360 P14-G P0 Silent Except Fix",
        "",
        f"- Mod: `{result['mode']}`",
        f"- Toplam düzeltilen sessiz except/pass bloğu: {result['total_silent_pass_blocks_patched']}",
    ]
    if result["backup_root"]:
        md.append(f"- Yedek: `{result['backup_root']}`")
    md.append("")
    md.append("## Hedefler")
    for item in result["targets"]:
        md.append(f"- `{item['path']}` changed={item['changed']} patched={len(item['block_changes'])}")
        for ch in item["block_changes"]:
            md.append(f"  - line {ch['line']}: `{ch['old_except_line'].strip()}`")
    write_text(report_md, "\n".join(md) + "\n")

    print(f"total_silent_pass_blocks_patched={result['total_silent_pass_blocks_patched']}")
    for item in result["targets"]:
        print(f"path={item['path']} changed={item['changed']} patched={len(item['block_changes'])}")
        for ch in item["block_changes"]:
            print(f"  line={ch['line']} old={ch['old_except_line'].strip()} new={ch['new_except_line'].strip()}")
    if result["backup_root"]:
        print(f"backup_root={result['backup_root']}")
    print(f"report_json={report_json}")
    print(f"report_md={report_md}")
    print("BYS360_QUALITY_10_10_P14_G_P0_SILENT_EXCEPT_FIX_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
