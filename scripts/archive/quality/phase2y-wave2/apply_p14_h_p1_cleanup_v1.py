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


EXCEPT_TARGETS = [
    {
        "path": "app/services/performance/period_delete_service.py",
        "label": "period_delete_service",
    },
    {
        "path": "app/services/performance/scoring_window_policy.py",
        "label": "scoring_window_policy",
    },
    {
        "path": "scripts/quality/apply_p14_e2_assistant_js_helper_split_safe_apply_v1.py",
        "label": "p14_e2_assistant_split",
    },
]

PREVIEW_FILES = [
    "reports/quality/bys360_quality_10_10_p14_e2_assistant_module_applied_preview.js",
    "reports/quality/bys360_quality_10_10_p14_e2_assistant_module_dryrun_preview.js",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def ensure_logging(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    updated = text

    if "import logging" not in updated:
        import_matches = list(re.finditer(r"^(?:import\s+.+|from\s+.+\s+import\s+.+)$", updated, flags=re.MULTILINE))
        if import_matches:
            last = import_matches[-1]
            insert_at = updated.find("\n", last.end())
            if insert_at >= 0:
                updated = updated[:insert_at + 1] + "import logging\n" + updated[insert_at + 1:]
            else:
                updated += "\nimport logging\n"
        else:
            updated = "import logging\n" + updated
        changes.append("import logging eklendi")

    if "LOGGER = logging.getLogger(__name__)" not in updated:
        import_matches = list(re.finditer(r"^(?:import\s+.+|from\s+.+\s+import\s+.+)$", updated, flags=re.MULTILINE))
        if import_matches:
            last = import_matches[-1]
            insert_at = updated.find("\n", last.end())
            if insert_at >= 0:
                updated = updated[:insert_at + 1] + "\nLOGGER = logging.getLogger(__name__)\n" + updated[insert_at + 1:]
            else:
                updated += "\n\nLOGGER = logging.getLogger(__name__)\n"
        else:
            updated = "LOGGER = logging.getLogger(__name__)\n" + updated
        changes.append("LOGGER eklendi")

    return updated, changes


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


def body_has_log_or_raise(body_text: str) -> bool:
    low = body_text.lower()
    return (
        "logger." in low
        or "logging." in low
        or re.search(r"^\s*raise\b", body_text, flags=re.MULTILINE) is not None
    )


def patch_unlogged_except_blocks(text: str, label: str) -> tuple[str, list[dict]]:
    lines = text.splitlines()
    blocks = [b for b in find_except_blocks(text) if not body_has_log_or_raise(b["body_text"])]

    if not blocks:
        return text, []

    block_map = {(b["start_index"], b["end_index"]): b for b in blocks}
    out: list[str] = []
    i = 0
    changes: list[dict] = []

    while i < len(lines):
        key = None
        for candidate_key in block_map:
            if i == candidate_key[0]:
                key = candidate_key
                break

        if key is None:
            out.append(lines[i])
            i += 1
            continue

        block = block_map[key]
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

        log_line = f'{body_indent}LOGGER.warning("BYS360 {label} işleminde yakalanan hata loglandı: %r", {exc_name})'

        out.append(new_except_line)
        out.append(log_line)
        out.extend(body)

        changes.append({
            "line": block["line"],
            "old_except_line": old_except_line,
            "new_except_line": new_except_line,
            "inserted_log": log_line,
        })
        i = key[1]

    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), changes


def compile_text(project_root: Path, rel_path: str, text: str) -> None:
    tmp = project_root / "reports" / "quality" / f"_p14h_compile_check_{Path(rel_path).name}"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    write_text(tmp, text)
    try:
        py_compile.compile(str(tmp), doraise=True)
    finally:
        try:
            tmp.unlink()
        except Exception as exc:
            LOGGER.warning("BYS360 P14-H self-cleanup işleminde yakalanan hata loglandı: %r", exc)
            pass


def apply(project_root: Path, dry_run: bool) -> dict:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"p14_h_p1_cleanup_{stamp}"

    result = {
        "mode": "DRY_RUN" if dry_run else "APPLY",
        "except_targets": [],
        "preview_files": [],
        "backup_root": str(backup_root) if not dry_run else None,
    }

    for target in EXCEPT_TARGETS:
        rel = target["path"]
        path = project_root / rel
        if not path.exists():
            raise SystemExit(f"TARGET_NOT_FOUND: {path}")

        original = read_text(path)
        updated, logging_changes = ensure_logging(original)
        updated, block_changes = patch_unlogged_except_blocks(updated, target["label"])
        if block_changes:
            compile_text(project_root, rel, updated)

        if not dry_run and updated != original:
            backup = backup_root / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)
            write_text(path, updated)

        result["except_targets"].append({
            "path": rel,
            "changed": updated != original,
            "logging_changes": logging_changes,
            "patched_blocks": block_changes,
            "patched_count": len(block_changes),
        })

    for rel in PREVIEW_FILES:
        src = project_root / rel
        dst = backup_root / rel if not dry_run else None
        item = {
            "path": rel,
            "exists": src.exists(),
            "moved_to_backup": False,
            "backup_path": str(dst) if dst else None,
        }

        if src.exists() and not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            item["moved_to_backup"] = True

        result["preview_files"].append(item)

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    print("BYS360_QUALITY_10_10_P14_H_P1_CLEANUP_START")
    print(f"project_root={project_root}")
    print(f"mode={'DRY_RUN' if args.dry_run else 'APPLY'}")

    result = apply(project_root, dry_run=args.dry_run)

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "dryrun" if args.dry_run else "applied"
    report_json = out_dir / f"bys360_quality_10_10_p14_h_p1_cleanup_{suffix}_v1.json"
    report_md = out_dir / f"bys360_quality_10_10_p14_h_p1_cleanup_{suffix}_v1.md"

    write_text(report_json, json.dumps(result, ensure_ascii=False, indent=2))

    md = [
        "# BYS360 P14-H P1 Cleanup",
        "",
        f"- Mod: `{result['mode']}`",
        f"- Yedek: `{result['backup_root']}`",
        "",
        "## EXCEPT_WITHOUT_LOG hedefleri",
    ]
    for item in result["except_targets"]:
        md.append(f"- `{item['path']}` changed={item['changed']} patched={item['patched_count']}")
        for block in item["patched_blocks"]:
            md.append(f"  - line {block['line']}: `{block['old_except_line'].strip()}`")
    md.append("")
    md.append("## Preview arşivleri")
    for item in result["preview_files"]:
        md.append(f"- `{item['path']}` exists={item['exists']} moved={item['moved_to_backup']}")
    write_text(report_md, "\n".join(md) + "\n")

    total_patched = sum(item["patched_count"] for item in result["except_targets"])
    total_moved = sum(1 for item in result["preview_files"] if item["moved_to_backup"])

    print(f"total_except_blocks_patched={total_patched}")
    print(f"total_preview_files_moved={total_moved}")
    print("BYS360_QUALITY_10_10_P14_H_EXCEPT_TARGETS")
    for item in result["except_targets"]:
        print(f"path={item['path']} changed={item['changed']} patched={item['patched_count']}")
        for block in item["patched_blocks"]:
            print(f"  line={block['line']} old={block['old_except_line'].strip()} new={block['new_except_line'].strip()}")
    print("BYS360_QUALITY_10_10_P14_H_PREVIEW_FILES")
    for item in result["preview_files"]:
        print(f"path={item['path']} exists={item['exists']} moved={item['moved_to_backup']} backup={item['backup_path']}")
    print(f"report_json={report_json}")
    print(f"report_md={report_md}")
    print("BYS360_QUALITY_10_10_P14_H_P1_CLEANUP_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
