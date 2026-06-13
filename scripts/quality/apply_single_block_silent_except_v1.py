from __future__ import annotations

import argparse
import ast
import datetime as _dt
import py_compile
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Block:
    except_line: int
    pass_line: int


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def find_simple_except_pass_blocks(text: str) -> list[Block]:
    ast.parse(text)
    lines = text.splitlines()
    blocks: list[Block] = []

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("except") and stripped.endswith(":"):
            j = idx + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and lines[j].strip() == "pass":
                blocks.append(Block(except_line=idx + 1, pass_line=j + 1))

    return blocks


def patch_one_block(text: str, rel_path: str, block_index: int) -> tuple[str, Block]:
    lines = text.splitlines(keepends=True)
    blocks = find_simple_except_pass_blocks(text)
    if not blocks:
        raise ValueError("NO_SIMPLE_EXCEPT_PASS_BLOCK")

    if block_index < 1 or block_index > len(blocks):
        raise ValueError(f"BLOCK_INDEX_OUT_OF_RANGE requested={block_index} available={len(blocks)}")

    target = blocks[block_index - 1]
    pass_line_idx = target.pass_line - 1
    pass_line = lines[pass_line_idx]
    indent = pass_line[: len(pass_line) - len(pass_line.lstrip())]

    replacement = (
        f'{indent}__import__("logging").getLogger(__name__).exception('
        f'"BYS360 kalite denetimi: sessiz except/pass yakalandi ({rel_path}:{target.pass_line})")\n'
    )
    lines[pass_line_idx] = replacement
    return "".join(lines), target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--block-index", type=int, default=1)
    parser.add_argument("--list-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    rel = args.target.replace("\\", "/").lstrip("./")
    target = (project_root / rel).resolve()

    print("BYS360_QUALITY_10_10_P5_SINGLE_BLOCK_START")
    print(f"project_root={project_root}")
    print(f"target={rel}")

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    original = read_text(target)

    try:
        blocks = find_simple_except_pass_blocks(original)
    except SyntaxError as exc:
        raise SystemExit(f"TARGET_SYNTAX_ERROR_BEFORE_PATCH: {exc}") from exc

    print(f"simple_blocks_found={len(blocks)}")
    for i, block in enumerate(blocks, start=1):
        print(f"block_index={i} except_line={block.except_line} pass_line={block.pass_line}")

    if args.list_only:
        print("BYS360_QUALITY_10_10_P5_SINGLE_BLOCK_LIST_OK")
        return 0

    if not blocks:
        print("BYS360_QUALITY_10_10_P5_SINGLE_BLOCK_NO_CHANGE")
        return 0

    patched_text, patched_block = patch_one_block(original, rel, args.block_index)

    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = project_root / ".quality_backup" / f"p5_single_block_{stamp}" / rel
    print(f"selected_block_index={args.block_index}")
    print(f"selected_pass_line={patched_block.pass_line}")
    print(f"backup_file={backup}")

    if args.dry_run:
        print("BYS360_QUALITY_10_10_P5_SINGLE_BLOCK_DRYRUN_OK")
        return 0

    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup)
    write_text(target, patched_text)

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as exc:
        shutil.copy2(backup, target)
        print("BYS360_QUALITY_10_10_P5_SINGLE_BLOCK_ROLLED_BACK")
        raise SystemExit(f"COMPILE_FAIL_RESTORED: {exc}") from exc

    print("BYS360_QUALITY_10_10_P5_SINGLE_BLOCK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
