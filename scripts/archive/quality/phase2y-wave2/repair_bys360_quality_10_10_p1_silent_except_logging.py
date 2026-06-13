# -*- coding: utf-8 -*-
"""
BYS360 QUALITY 10/10 - P1 Silent Except Logging Repair

Amaç:
- except bloğu içinde yalnızca pass bulunan sessiz hata yutma noktalarını loglanabilir hale getirir.
- Davranışı değiştirmez: hata yine yutulur, fakat artık logger.exception ile kayıt altına alınır.
- Dosyaları değiştirmeden önce .quality_backup altında yedekler.

Kullanım:
python scripts/quality/repair_bys360_quality_10_10_p1_silent_except_logging.py --project-root C:\\bys360\\project --paths app scripts
"""
from __future__ import annotations

import argparse
import datetime as _dt
import pathlib
import re
import shutil
import sys
from dataclasses import dataclass

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    "node_modules", "dist", "build", "reports", ".quality_backup",
}

EXCLUDED_FILE_PARTS = {
    # Kalite aracının kendi kendisini değiştirmesini engelleyelim.
    "scripts/quality/repair_bys360_quality_10_10_p1_silent_except_logging.py",
}

EXCEPT_RE = re.compile(r"^(?P<indent>[ \t]*)except(?:\s+[^:]*)?:\s*(?:#.*)?$")
PASS_RE = re.compile(r"^(?P<indent>[ \t]*)pass\s*(?:#.*)?$")
COMMENT_OR_BLANK_RE = re.compile(r"^[ \t]*(?:#.*)?$")
LOGGER_DEF_RE = re.compile(r"^[ \t]*(logger|LOGGER)\s*=\s*logging\.getLogger\(")
IMPORT_LOGGING_RE = re.compile(r"^[ \t]*import\s+logging\b|^[ \t]*from\s+logging\s+import\s+")


@dataclass
class PatchResult:
    path: pathlib.Path
    replacements: int


def _is_excluded(path: pathlib.Path, root: pathlib.Path) -> bool:
    rel = path.relative_to(root).as_posix()
    if rel in EXCLUDED_FILE_PARTS:
        return True
    return any(part in EXCLUDED_DIRS for part in path.parts)


def _iter_python_files(root: pathlib.Path, relative_paths: list[str]) -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for rel in relative_paths:
        base = (root / rel).resolve()
        if not base.exists():
            continue
        if base.is_file() and base.suffix == ".py" and not _is_excluded(base, root):
            files.append(base)
            continue
        if base.is_dir():
            for p in base.rglob("*.py"):
                if not _is_excluded(p.resolve(), root):
                    files.append(p.resolve())
    return sorted(set(files))


def _detect_newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def _has_logger(lines: list[str]) -> bool:
    return any(LOGGER_DEF_RE.search(line) for line in lines)


def _has_import_logging(lines: list[str]) -> bool:
    return any(IMPORT_LOGGING_RE.search(line) for line in lines)


def _line_indent_width(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _insert_logging_boilerplate(lines: list[str], newline: str) -> list[str]:
    if _has_logger(lines):
        return lines

    has_import_logging = _has_import_logging(lines)
    out = list(lines)

    # 1) import logging yoksa güvenli bir yere ekle.
    if not has_import_logging:
        insert_at = 0

        # shebang / encoding satırlarını geç
        while insert_at < len(out) and (
            out[insert_at].startswith("#!") or "coding" in out[insert_at][:80]
        ):
            insert_at += 1

        # modül docstring'i varsa geç
        if insert_at < len(out) and out[insert_at].lstrip().startswith(('"""', "'''")):
            quote = '"""' if out[insert_at].lstrip().startswith('"""') else "'''"
            if out[insert_at].count(quote) >= 2 and out[insert_at].strip() != quote:
                insert_at += 1
            else:
                insert_at += 1
                while insert_at < len(out) and quote not in out[insert_at]:
                    insert_at += 1
                if insert_at < len(out):
                    insert_at += 1

        # __future__ importları varsa onlardan sonra ekle
        while insert_at < len(out) and (
            out[insert_at].strip() == "" or out[insert_at].startswith("from __future__ import")
        ):
            insert_at += 1

        out.insert(insert_at, f"import logging{newline}")

    # 2) logger tanımını import bloğunun sonuna ekle.
    if not _has_logger(out):
        last_import_idx = None
        for idx, line in enumerate(out):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                last_import_idx = idx
        if last_import_idx is None:
            out.insert(0, f"import logging{newline}")
            last_import_idx = 0
        out.insert(last_import_idx + 1, f"logger = logging.getLogger(__name__){newline}")

    return out


def _patch_silent_except_blocks(lines: list[str], newline: str, rel_path: str) -> tuple[list[str], int]:
    out = list(lines)
    replacements = 0
    i = 0

    while i < len(out):
        m = EXCEPT_RE.match(out[i])
        if not m:
            i += 1
            continue

        except_indent = m.group("indent")
        j = i + 1
        body_indices: list[int] = []

        while j < len(out):
            line = out[j]
            if line.strip() == "":
                body_indices.append(j)
                j += 1
                continue

            indent_width = _line_indent_width(line)
            except_indent_width = len(except_indent)

            # Yeni blok başladı.
            if indent_width <= except_indent_width and line.strip():
                break

            body_indices.append(j)
            j += 1

        if not body_indices:
            i += 1
            continue

        non_comment = [idx for idx in body_indices if not COMMENT_OR_BLANK_RE.match(out[idx])]
        if len(non_comment) == 1 and PASS_RE.match(out[non_comment[0]]):
            pass_idx = non_comment[0]
            pass_indent = PASS_RE.match(out[pass_idx]).group("indent")  # type: ignore[union-attr]
            message = (
                f'{pass_indent}logger.exception('
                f'"BYS360 kalite denetimi: sessiz except bloğu loglandı: {rel_path}:{i + 1}")'
                f'{newline}'
            )
            out[pass_idx] = message
            replacements += 1
            i = j
            continue

        i += 1

    return out, replacements


def patch_file(path: pathlib.Path, root: pathlib.Path, backup_root: pathlib.Path, dry_run: bool = False) -> PatchResult:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        text = raw.decode("utf-8-sig")
        encoding = "utf-8-sig"

    newline = _detect_newline(text)
    lines = text.splitlines(keepends=True)
    rel = path.relative_to(root).as_posix()

    patched, replacements = _patch_silent_except_blocks(lines, newline, rel)
    if replacements <= 0:
        return PatchResult(path=path, replacements=0)

    patched = _insert_logging_boilerplate(patched, newline)
    new_text = "".join(patched)

    if new_text != text and not dry_run:
        backup_path = backup_root / rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)
        path.write_text(new_text, encoding=encoding, newline="")

    return PatchResult(path=path, replacements=replacements)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--paths", nargs="+", default=["app", "scripts"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    root = pathlib.Path(args.project_root).resolve()
    if not root.exists():
        print(f"BYS360_QUALITY_P1_FAIL project root not found: {root}")
        return 2

    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = root / ".quality_backup" / f"silent_except_logging_v1_{stamp}"

    files = _iter_python_files(root, args.paths)
    results: list[PatchResult] = []
    for file_path in files:
        try:
            result = patch_file(file_path, root, backup_root, dry_run=args.dry_run)
            if result.replacements:
                results.append(result)
        except Exception as exc:  # noqa: BLE001 - repair aracı hatayı görünür yapmalı
            print(f"[WARN] patch skipped: {file_path}: {exc}")

    total = sum(r.replacements for r in results)
    print("BYS360_QUALITY_10_10_P1_SILENT_EXCEPT_REPAIR_SUMMARY")
    print(f"files_scanned={len(files)}")
    print(f"files_changed={len(results)}")
    print(f"silent_except_blocks_patched={total}")
    if not args.dry_run:
        print(f"backup_root={backup_root}")
    for r in results[:80]:
        print(f" - {r.path.relative_to(root).as_posix()} :: {r.replacements}")
    if len(results) > 80:
        print(f"... {len(results) - 80} ek dosya değişti")
    print("BYS360_QUALITY_10_10_P1_SILENT_EXCEPT_REPAIR_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
