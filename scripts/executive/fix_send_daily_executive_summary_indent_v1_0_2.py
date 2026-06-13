# -*- coding: utf-8 -*-
"""
BYS360 V1.0.2 - send_daily_executive_summary.py IndentationError fixer
Amaç: Günlük hava maili kurulumunu engelleyen mevcut yönetici özeti scriptindeki
beklenmeyen girinti hatasını güvenli şekilde düzeltmek.
"""
from __future__ import annotations

import argparse
import json
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

VERSION = "BYS360_DAILY_WEATHER_MAIL_V1_0_2_EXEC_INDENT_FIX"
REL = Path("scripts") / "executive" / "send_daily_executive_summary.py"


def compile_file(path: Path) -> Tuple[bool, Optional[BaseException]]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, None
    except BaseException as exc:  # noqa: BLE001 - kullanıcıya kontrollü raporlanacak
        return False, exc


def leading_spaces(s: str) -> int:
    expanded = s.expandtabs(4)
    return len(expanded) - len(expanded.lstrip(" "))


def set_indent(line: str, indent: int) -> str:
    stripped = line.lstrip(" \t")
    return (" " * max(0, indent)) + stripped


def previous_code_line(lines: List[str], idx0: int) -> Tuple[int, str]:
    for j in range(idx0 - 1, -1, -1):
        text = lines[j].strip()
        if text and not text.startswith("#"):
            return j, lines[j]
    return -1, ""


def expected_indent_from_previous(prev: str) -> int:
    if not prev:
        return 0
    base = leading_spaces(prev)
    stripped = prev.strip()
    if stripped.endswith(":"):
        return base + 4
    return base


def try_write_and_compile(path: Path, original: List[str], candidate: List[str]) -> bool:
    path.write_text("".join(candidate), encoding="utf-8")
    ok, _ = compile_file(path)
    if not ok:
        path.write_text("".join(original), encoding="utf-8")
    return ok


def build_context(lines: List[str], lineno: int, radius: int = 8) -> List[str]:
    out = []
    start = max(1, lineno - radius)
    end = min(len(lines), lineno + radius)
    for n in range(start, end + 1):
        marker = "<--" if n == lineno else "   "
        out.append(f"{n:04d} {marker} {lines[n-1].rstrip()}")
    return out


def repair(path: Path) -> dict:
    result = {
        "version": VERSION,
        "file": str(path),
        "already_ok": False,
        "repaired": False,
        "strategy": None,
        "error_before": None,
        "error_after": None,
        "backup": None,
        "context": [],
    }

    if not path.exists():
        result["error_after"] = f"Dosya bulunamadı: {path}"
        return result

    ok, exc = compile_file(path)
    if ok:
        result["already_ok"] = True
        return result

    result["error_before"] = repr(exc)
    lineno = int(getattr(exc, "lineno", 0) or 0)
    if lineno <= 0:
        result["error_after"] = "Hata satırı tespit edilemedi; dosya değiştirilmedi."
        return result

    original_text = path.read_text(encoding="utf-8", errors="replace")
    original = original_text.splitlines(keepends=True)
    if lineno > len(original):
        result["error_after"] = "Hata satırı dosya uzunluğunu aşıyor; dosya değiştirilmedi."
        return result

    result["context"] = build_context(original, lineno)

    backup_dir = path.parent / "_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"{path.name}.{stamp}.bak"
    shutil.copy2(path, backup)
    result["backup"] = str(backup)

    idx = lineno - 1
    prev_idx, prev_line = previous_code_line(original, idx)
    current_indent = leading_spaces(original[idx])
    expected = expected_indent_from_previous(prev_line)
    prev_indent = leading_spaces(prev_line) if prev_line else 0

    candidates = []
    for target in [expected, prev_indent, 0, 4, 8]:
        if target != current_indent:
            candidate = original[:]
            candidate[idx] = set_indent(candidate[idx], target)
            candidates.append((f"single_line_indent_to_{target}", candidate))

    # Blok halinde fazla girintilenmiş satırları azaltmayı dene.
    block_end = idx
    for j in range(idx + 1, len(original)):
        stripped = original[j].strip()
        if not stripped:
            block_end = j
            continue
        ind = leading_spaces(original[j])
        if ind >= current_indent:
            block_end = j
            continue
        break

    for target in [expected, prev_indent, 0, 4, 8]:
        if target < current_indent:
            delta = current_indent - target
            candidate = original[:]
            for j in range(idx, block_end + 1):
                if candidate[j].strip():
                    ind = leading_spaces(candidate[j])
                    if ind >= current_indent:
                        candidate[j] = set_indent(candidate[j], max(0, ind - delta))
            candidates.append((f"block_{idx+1}_{block_end+1}_dedent_to_{target}", candidate))

    for strategy, candidate in candidates:
        if try_write_and_compile(path, original, candidate):
            result["repaired"] = True
            result["strategy"] = strategy
            return result

    # Başaramazsa dosyayı geri yükle.
    path.write_text(original_text, encoding="utf-8")
    ok2, exc2 = compile_file(path)
    result["error_after"] = repr(exc2) if exc2 else "Düzeltme uygulanamadı; dosya orijinal haliyle bırakıldı."
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    path = root / REL
    res = repair(path)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if (res.get("already_ok") or res.get("repaired")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
