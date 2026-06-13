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


TARGET_REL = "scripts/quality/apply_p14_g_p0_silent_except_fix_v1.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def ensure_logging(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    updated = text

    if "import logging" not in updated:
        # Put logging near imports.
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


def find_silent_except_pass_blocks(text: str) -> list[dict]:
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

        useful = [b.strip() for b in body if b.strip() and not b.strip().startswith("#")]
        if useful == ["pass"]:
            blocks.append({
                "start_index": i,
                "end_index": j,
                "line": i + 1,
                "except_line": line,
                "expr": (m.group("expr") or "").strip(),
                "indent": indent,
                "body": body,
            })
        i = j

    return blocks


def patch_blocks(text: str) -> tuple[str, list[dict]]:
    lines = text.splitlines()
    blocks = find_silent_except_pass_blocks(text)
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

        body_indent = indent + "    "
        for body_line in block["body"]:
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

        log_line = f'{body_indent}LOGGER.warning("BYS360 P14-G self-check temizleme sırasında bastırılan hata loglandı: %r", {exc_name})'

        out.append(new_except_line)
        out.append(log_line)

        changes.append({
            "line": block["line"],
            "old_except_line": old_except_line,
            "new_except_line": new_except_line,
            "new_body": log_line,
        })
        i = key[1]

    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), changes


def compile_text(project_root: Path, text: str) -> None:
    tmp = project_root / "reports" / "quality" / "_p14g2_self_compile_check.py"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    write_text(tmp, text)
    try:
        py_compile.compile(str(tmp), doraise=True)
    finally:
        try:
            tmp.unlink()
        except Exception as exc:
            LOGGER.warning("BYS360 P14-G2 temp compile dosyası silinemedi: %r", exc)


def apply(project_root: Path, dry_run: bool) -> dict:
    target = project_root / TARGET_REL
    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    original = read_text(target)
    updated, logging_changes = ensure_logging(original)
    updated, block_changes = patch_blocks(updated)

    if not block_changes:
        raise SystemExit("NO_SILENT_EXCEPT_PASS_BLOCK_FOUND_IN_P14_G_SCRIPT")

    compile_text(project_root, updated)

    backup_root = None
    if not dry_run and updated != original:
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root_path = project_root / ".quality_backup" / f"p14_g2_self_p0_fix_{stamp}"
        backup = backup_root_path / TARGET_REL
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
        write_text(target, updated)
        backup_root = str(backup_root_path)

    return {
        "mode": "DRY_RUN" if dry_run else "APPLY",
        "target": TARGET_REL,
        "changed": updated != original,
        "logging_changes": logging_changes,
        "block_changes": block_changes,
        "patched_count": len(block_changes),
        "backup_root": backup_root,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    print("BYS360_QUALITY_10_10_P14_G2_SELF_P0_FIX_START")
    print(f"project_root={project_root}")
    print(f"mode={'DRY_RUN' if args.dry_run else 'APPLY'}")

    result = apply(project_root, dry_run=args.dry_run)

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "dryrun" if args.dry_run else "applied"
    report_json = out_dir / f"bys360_quality_10_10_p14_g2_self_p0_fix_{suffix}_v1.json"
    report_md = out_dir / f"bys360_quality_10_10_p14_g2_self_p0_fix_{suffix}_v1.md"

    write_text(report_json, json.dumps(result, ensure_ascii=False, indent=2))

    md = [
        "# BYS360 P14-G2 Self P0 Fix",
        "",
        f"- Mod: `{result['mode']}`",
        f"- Hedef: `{TARGET_REL}`",
        f"- Değişti: {result['changed']}",
        f"- Düzeltilen blok: {result['patched_count']}",
    ]
    if result["backup_root"]:
        md.append(f"- Yedek: `{result['backup_root']}`")
    md.append("")
    md.append("## Bloklar")
    for item in result["block_changes"]:
        md.append(f"- line {item['line']}: `{item['old_except_line'].strip()}` → `{item['new_except_line'].strip()}`")
    write_text(report_md, "\n".join(md) + "\n")

    print(f"changed={result['changed']}")
    print(f"patched_count={result['patched_count']}")
    for item in result["block_changes"]:
        print(f"line={item['line']} old={item['old_except_line'].strip()} new={item['new_except_line'].strip()}")
    if result["backup_root"]:
        print(f"backup_root={result['backup_root']}")
    print(f"report_json={report_json}")
    print(f"report_md={report_md}")
    print("BYS360_QUALITY_10_10_P14_G2_SELF_P0_FIX_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
