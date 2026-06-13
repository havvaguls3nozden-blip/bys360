from __future__ import annotations

import argparse
import datetime as _dt
import py_compile
import shutil
from pathlib import Path


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def patch_silent_except_pass(text: str, rel_path: str) -> tuple[str, int]:
    """
    Very conservative patch:
    - Only patches a line that is exactly/only `pass` immediately after an `except ...:` line.
    - Does not insert imports.
    - Uses __import__("logging") to avoid touching future imports/import order.
    - Keeps indentation exactly based on the original pass line.
    """
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    patched = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("except") and stripped.endswith(":"):
            out.append(line)
            j = i + 1

            # Preserve blank lines directly after except, if any.
            blanks: list[str] = []
            while j < len(lines) and lines[j].strip() == "":
                blanks.append(lines[j])
                j += 1

            if j < len(lines) and lines[j].strip() == "pass":
                pass_line = lines[j]
                indent = pass_line[: len(pass_line) - len(pass_line.lstrip())]
                out.extend(blanks)
                message = f'BYS360 kalite denetimi: sessiz except/pass yakalandi ({rel_path})'
                out.append(f'{indent}__import__("logging").getLogger(__name__).exception("{message}")\n')
                patched += 1
                i = j + 1
                continue

            out.extend(blanks)
            i = j
            continue

        out.append(line)
        i += 1

    return "".join(out), patched


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--target", default="app/live_scope.py")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target_rel = args.target.replace("\\", "/")
    target = (project_root / target_rel).resolve()

    print("BYS360_QUALITY_10_10_P2_SINGLE_FILE_PATCH_START")
    print(f"project_root={project_root}")
    print(f"target={target_rel}")

    if not target.exists():
        raise SystemExit(f"HEDEF_DOSYA_YOK: {target}")

    original = _read(target)
    patched_text, patched_count = patch_silent_except_pass(original, target_rel)

    print(f"silent_except_blocks_found={patched_count}")

    if patched_count == 0:
        print("BYS360_QUALITY_10_10_P2_SINGLE_FILE_PATCH_NO_CHANGE")
        return 0

    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"single_file_silent_except_v1_{stamp}"
    backup_path = backup_root / target_rel
    print(f"backup_root={backup_root}")

    if args.dry_run:
        print("BYS360_QUALITY_10_10_P2_SINGLE_FILE_PATCH_DRYRUN_OK")
        return 0

    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup_path)

    _write(target, patched_text)

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as exc:
        shutil.copy2(backup_path, target)
        print("BYS360_QUALITY_10_10_P2_SINGLE_FILE_PATCH_ROLLED_BACK")
        raise SystemExit(f"COMPILE_FAIL_RESTORED: {exc}") from exc

    print("BYS360_QUALITY_10_10_P2_SINGLE_FILE_PATCH_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
