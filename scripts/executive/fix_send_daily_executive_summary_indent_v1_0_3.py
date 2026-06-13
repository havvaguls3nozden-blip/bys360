# -*- coding: utf-8 -*-
"""
BYS360 V1.0.3 - send_daily_executive_summary.py compile/indent fixer

Amaç:
- Günlük hava maili kurulumu tamamlandıktan sonra global compileall'i düşüren
  mevcut scripts/executive/send_daily_executive_summary.py dosyasındaki
  IndentationError sorununu güvenli şekilde düzeltmek.
- Önce noktasal girinti düzeltmesi dener.
- Olmazsa dosyanın main bloğunu standart, derlenebilir bir main bloğu ile yeniler.
"""
from __future__ import annotations

import argparse
import json
import py_compile
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Tuple

VERSION = "BYS360_DAILY_WEATHER_MAIL_V1_0_3_EXEC_SUMMARY_COMPILE_FIX"
REL = Path("scripts") / "executive" / "send_daily_executive_summary.py"


def compile_file(path: Path) -> Tuple[bool, Optional[BaseException]]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, None
    except BaseException as exc:  # noqa: BLE001
        return False, exc


def extract_lineno(exc: BaseException) -> int:
    """py_compile.PyCompileError içinde gömülü SyntaxError/IndentationError satırını yakala."""
    # PyCompileError usually has exc_value.
    inner = getattr(exc, "exc_value", None)
    if inner is not None:
        lineno = getattr(inner, "lineno", None)
        if lineno:
            return int(lineno)
    for attr in ("lineno",):
        lineno = getattr(exc, attr, None)
        if lineno:
            return int(lineno)
    text = repr(exc)
    # Examples: "line 54" or "..., 54, 4, ..."
    m = re.search(r"line\s+(\d+)", text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"send_daily_executive_summary\.py',\s*(\d+),", text)
    if m:
        return int(m.group(1))
    return 0


def leading_spaces(s: str) -> int:
    expanded = s.expandtabs(4)
    return len(expanded) - len(expanded.lstrip(" "))


def set_indent(line: str, indent: int) -> str:
    return (" " * max(0, indent)) + line.lstrip(" \t")


def build_context(lines: List[str], lineno: int, radius: int = 10) -> List[str]:
    out: List[str] = []
    if lineno <= 0:
        return out
    start = max(1, lineno - radius)
    end = min(len(lines), lineno + radius)
    for n in range(start, end + 1):
        marker = "<--" if n == lineno else "   "
        out.append(f"{n:04d} {marker} {lines[n - 1].rstrip()}")
    return out


def try_candidate(path: Path, original_text: str, candidate: List[str]) -> Tuple[bool, Optional[str]]:
    path.write_text("".join(candidate), encoding="utf-8")
    ok, exc = compile_file(path)
    if ok:
        return True, None
    path.write_text(original_text, encoding="utf-8")
    return False, repr(exc)


def line_reindent_attempts(path: Path, lines: List[str], lineno: int, original_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    if lineno <= 0 or lineno > len(lines):
        return False, None, "Hata satırı güvenilir biçimde tespit edilemedi."

    idx = lineno - 1
    current_indent = leading_spaces(lines[idx])

    # Önce sadece hata satırını farklı olası seviyelere çek.
    for target in [0, 4, 8, 12, 16]:
        if target == current_indent:
            continue
        candidate = lines[:]
        candidate[idx] = set_indent(candidate[idx], target)
        ok, err = try_candidate(path, original_text, candidate)
        if ok:
            return True, f"single_line_indent_to_{target}", None

    # Sonra aynı/fazla girintili devam eden küçük bloğu birlikte düzelt.
    block_end = idx
    for j in range(idx + 1, min(len(lines), idx + 25)):
        if not lines[j].strip():
            block_end = j
            continue
        ind = leading_spaces(lines[j])
        if ind >= current_indent:
            block_end = j
            continue
        break

    for target in [0, 4, 8, 12]:
        delta = current_indent - target
        if delta <= 0:
            continue
        candidate = lines[:]
        for j in range(idx, block_end + 1):
            if candidate[j].strip() and leading_spaces(candidate[j]) >= current_indent:
                candidate[j] = set_indent(candidate[j], max(0, leading_spaces(candidate[j]) - delta))
        ok, err = try_candidate(path, original_text, candidate)
        if ok:
            return True, f"block_{idx+1}_{block_end+1}_dedent_to_{target}", None

    return False, None, "Noktasal girinti düzeltmeleri derleme hatasını gidermedi."


def find_def_main(lines: List[str]) -> int:
    for i, line in enumerate(lines):
        if re.match(r"^def\s+main\s*\(", line):
            return i
    return -1


def find_if_name_main(lines: List[str]) -> int:
    for i, line in enumerate(lines):
        if re.match(r"^if\s+__name__\s*==\s*['\"]__main__['\"]\s*:", line):
            return i
    return -1


def detect_default_type(text: str) -> str:
    # Mevcut dosyada report_type default/choices varsa mümkün olduğunca koru.
    m = re.search(r"default\s*=\s*['\"]([A-Za-z0-9_\-]+)['\"]", text)
    if m:
        val = m.group(1)
        if val in {"morning", "night", "evening", "daily", "summary"}:
            return val
    return "morning"


def build_safe_main(default_type: str) -> str:
    return f'''

def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="BYS360 günlük yönetici özeti mail gönderimi")
    parser.add_argument("--type", default="{default_type}", help="Özet türü: morning/night/evening/daily")
    parser.add_argument("--manual", action="store_true", help="Manuel çalıştırma olarak işaretle")
    parser.add_argument("--dry-run", action="store_true", help="Mail göndermeden kontrol et")
    args = parser.parse_args()

    if args.dry_run:
        print(json.dumps({{"ok": True, "dry_run": True, "type": args.type}}, ensure_ascii=False))
        return 0

    result = send_executive_summary_email(report_type=args.type, manual=args.manual)

    if isinstance(result, dict):
        print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
        return 0 if result.get("ok", True) else 1

    if result is not None:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''.lstrip("\n")


def main_block_rewrite_attempt(path: Path, lines: List[str], original_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    if "send_executive_summary_email" not in original_text:
        return False, None, "Dosyada send_executive_summary_email adı bulunamadı; main bloğu güvenli yenilenmedi."

    start = find_def_main(lines)
    strategy = "rewrite_def_main_to_end"
    if start < 0:
        start = find_if_name_main(lines)
        strategy = "insert_main_before_if_name_main"
    if start < 0:
        # Son çare: dosya sonuna main ekle. Önce bozuk main satırlarını atamayacağı için yalnızca
        # hata satırı result=... ve sonrasını bulabilirsek kes.
        for i, line in enumerate(lines):
            if "send_executive_summary_email(" in line and "result" in line:
                start = i
                strategy = "rewrite_from_first_result_call_to_end"
                break
    if start < 0:
        return False, None, "main başlangıcı tespit edilemedi."

    default_type = detect_default_type(original_text)
    candidate = lines[:start]
    if candidate and candidate[-1].strip():
        candidate.append("\n")
    candidate.append(build_safe_main(default_type))

    ok, err = try_candidate(path, original_text, candidate)
    if ok:
        return True, strategy, None
    return False, None, err or "main bloğu yenilendi ancak derleme geçmedi."


def repair(path: Path) -> dict[str, Any]:
    res: dict[str, Any] = {
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
        res["error_after"] = f"Dosya bulunamadı: {path}"
        return res

    ok, exc = compile_file(path)
    if ok:
        res["already_ok"] = True
        return res

    res["error_before"] = repr(exc)
    lineno = extract_lineno(exc) if exc else 0

    original_text = path.read_text(encoding="utf-8", errors="replace")
    lines = original_text.splitlines(keepends=True)
    res["context"] = build_context(lines, lineno)

    backup_dir = path.parent / "_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"{path.name}.{stamp}.v1_0_3.bak"
    shutil.copy2(path, backup)
    res["backup"] = str(backup)

    ok1, strategy1, err1 = line_reindent_attempts(path, lines, lineno, original_text)
    if ok1:
        res["repaired"] = True
        res["strategy"] = strategy1
        return res

    # Orijinali tekrar yükle ve main bloğu yenilemeyi dene.
    path.write_text(original_text, encoding="utf-8")
    ok2, strategy2, err2 = main_block_rewrite_attempt(path, lines, original_text)
    if ok2:
        res["repaired"] = True
        res["strategy"] = strategy2
        return res

    path.write_text(original_text, encoding="utf-8")
    ok_after, exc_after = compile_file(path)
    res["error_after"] = err2 or err1 or (repr(exc_after) if exc_after else "Düzeltme uygulanamadı.")
    return res


def cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    res = repair(root / REL)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if (res.get("already_ok") or res.get("repaired")) else 1


if __name__ == "__main__":
    raise SystemExit(cli())
