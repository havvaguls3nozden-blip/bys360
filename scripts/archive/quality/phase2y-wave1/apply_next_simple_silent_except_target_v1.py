from __future__ import annotations

import argparse
import ast
import datetime as _dt
import py_compile
import shutil
import subprocess
from pathlib import Path

EXCLUDE_PARTS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".quality_backup",
    "node_modules",
    "build",
    "dist",
}

EXCLUDE_PATH_TOKENS = (
    "versions_BACKUP",
    "versions_backup",
    "BACKUP_BEFORE",
    "backup_before",
)


def is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDE_PARTS:
        return True
    raw = str(path)
    return any(token in raw for token in EXCLUDE_PATH_TOKENS)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def simple_except_pass_count(path: Path) -> int:
    text = read_text(path)
    try:
        ast.parse(text)
    except SyntaxError:
        return 0

    lines = text.splitlines()
    count = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("except") and stripped.endswith(":"):
            j = idx + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and lines[j].strip() == "pass":
                count += 1
    return count


def patch_text(text: str, rel: str) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    output: list[str] = []
    patched = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("except") and stripped.endswith(":"):
            output.append(line)
            j = i + 1
            blanks: list[str] = []
            while j < len(lines) and lines[j].strip() == "":
                blanks.append(lines[j])
                j += 1

            if j < len(lines) and lines[j].strip() == "pass":
                pass_line = lines[j]
                indent = pass_line[: len(pass_line) - len(pass_line.lstrip())]
                output.extend(blanks)
                output.append(
                    f'{indent}__import__("logging").getLogger(__name__).exception('
                    f'"BYS360 kalite denetimi: sessiz except/pass yakalandi ({rel})")\n'
                )
                patched += 1
                i = j + 1
                continue

            output.extend(blanks)
            i = j
            continue

        output.append(line)
        i += 1

    return "".join(output), patched


def choose_target(project_root: Path) -> Path | None:
    candidates: list[tuple[int, str, Path]] = []
    for path in project_root.rglob("*.py"):
        rel_path = path.relative_to(project_root)
        if is_excluded(rel_path):
            continue
        count = simple_except_pass_count(path)
        if count:
            rel = rel_path.as_posix()
            # Prefer single-block smaller/non-risky files before large central registries.
            risk = 0
            if rel in {"app/menu_registry.py", "app/api/mobile/routes.py", "app/api/mobile/performance_routes.py"}:
                risk = 10
            if rel.startswith("migrations/"):
                risk = 8
            candidates.append((risk * 1000 + count, rel, path))

    candidates.sort(key=lambda item: (item[0], len(item[1]), item[1]))
    return candidates[0][2] if candidates else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--target", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target = (project_root / args.target).resolve() if args.target else choose_target(project_root)

    print("BYS360_QUALITY_10_10_P4_APPLY_ONE_START")
    print(f"project_root={project_root}")

    if target is None or not target.exists():
        print("BYS360_QUALITY_10_10_P4_APPLY_ONE_NO_TARGET")
        return 0

    rel = target.relative_to(project_root).as_posix()
    print(f"target={rel}")

    original = read_text(target)
    patched_text, patched_count = patch_text(original, rel)
    print(f"silent_except_blocks_found={patched_count}")

    if patched_count == 0:
        print("BYS360_QUALITY_10_10_P4_APPLY_ONE_NO_CHANGE")
        return 0

    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = project_root / ".quality_backup" / f"p4_apply_one_{stamp}" / rel
    print(f"backup_file={backup}")

    if args.dry_run:
        print("BYS360_QUALITY_10_10_P4_APPLY_ONE_DRYRUN_OK")
        return 0

    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup)
    write_text(target, patched_text)

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as exc:
        shutil.copy2(backup, target)
        print("BYS360_QUALITY_10_10_P4_APPLY_ONE_ROLLED_BACK")
        raise SystemExit(f"COMPILE_FAIL_RESTORED: {exc}") from exc

    print("BYS360_QUALITY_10_10_P4_APPLY_ONE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
