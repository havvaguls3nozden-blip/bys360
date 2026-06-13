from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import List, Tuple

PACKAGE = "BYS360_QUALITY9_FUTURE_DOCSTRING_SYNTAX_HOTFIX_V7"
FUTURE_LINE = "from __future__ import annotations"
CODING_RE = re.compile(r"coding[:=]\s*[-\w.]+")
LOGGING_GETLOGGER_RE = re.compile(r"\blogging\.getLogger\b")
LOGGING_IMPORT_RE = re.compile(r"^\s*(import\s+logging\b|from\s+logging\s+import\s+)", re.M)

V5_RETIRED_TEXT = '''from __future__ import annotations

import argparse
import json
from pathlib import Path

PACKAGE = "BYS360_QUALITY9_FUTURE_DOCSTRING_SYNTAX_HOTFIX_V5_RETIRED"


def main() -> int:
    parser = argparse.ArgumentParser(description="Retired BYS360 V5 hotfix wrapper.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--mode", default="all")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    payload = {
        "package": PACKAGE,
        "ok": True,
        "status": "retired_superseded_by_v6_v7",
        "project_root": str(root),
        "mode": args.mode,
        "dry_run": bool(args.dry_run),
        "changed_count": 0,
        "finding_count": 0,
        "note": "This wrapper replaces the broken V5 repair script so compileall can pass. Use V6/V7 scripts for actual repair.",
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def read_text(path: Path) -> Tuple[str, str]:
    raw = path.read_bytes()
    newline = "\r\n" if b"\r\n" in raw[:4096] else "\n"
    for encoding in ("utf-8-sig", "utf-8", "cp1254"):
        try:
            return raw.decode(encoding), newline
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), newline


def write_text(path: Path, text: str, newline: str = "\n") -> None:
    text = text.replace("\r\n", "\n")
    if newline == "\r\n":
        text = text.replace("\n", "\r\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def split_lines_keep(text: str) -> List[str]:
    return text.splitlines(True) if text else []


def has_line_end(line: str) -> bool:
    return line.endswith("\n") or line.endswith("\r\n")


def ensure_line_end(line: str, newline: str) -> str:
    if has_line_end(line):
        return line
    return line + newline


def strip_line_end(line: str) -> str:
    return line.rstrip("\r\n")


def is_future_line(line: str) -> bool:
    return line.strip() == FUTURE_LINE


def retire_broken_v5_script(root: Path, dry_run: bool = False) -> dict:
    path = root / "scripts" / "quality" / "repair_bys360_quality9_future_docstring_syntax_hotfix_v5.py"
    current = None
    newline = "\n"
    if path.exists():
        current, newline = read_text(path)
    changed = current != V5_RETIRED_TEXT
    if changed and not dry_run:
        write_text(path, V5_RETIRED_TEXT, newline)
    return {"file": str(path), "changed": changed, "action": "retire_broken_v5_script"}


def repair_concatenated_future_lines(text: str, newline: str) -> Tuple[str, List[dict]]:
    lines = split_lines_keep(text)
    if not lines:
        return text, []

    changed: List[dict] = []
    out: List[str] = []
    quote_markers = ('"' * 3, "'" * 3)

    for line_no, line in enumerate(lines, start=1):
        if FUTURE_LINE not in line or is_future_line(line):
            out.append(line)
            continue

        before, after = line.split(FUTURE_LINE, 1)
        before_clean = strip_line_end(before)
        after_clean = strip_line_end(after)
        before_rstrip = before_clean.rstrip()
        after_lstrip = after_clean.lstrip()
        repaired = False

        if before_clean and any(before_rstrip.endswith(marker) for marker in quote_markers):
            out.append(ensure_line_end(before_clean, newline))
            future_line = FUTURE_LINE + after
            if not has_line_end(future_line):
                future_line += newline
            out.append(future_line)
            repaired = True
        elif after_clean and any(after_lstrip.startswith(marker) for marker in quote_markers):
            out.append(FUTURE_LINE + newline)
            out.append(after_clean + ("" if has_line_end(line) else newline))
            repaired = True

        if repaired:
            changed.append({"line": line_no, "status": "split_concatenated_future_import"})
        else:
            out.append(line)

    return "".join(out), changed


def skip_preamble(lines: List[str]) -> int:
    idx = 0
    if idx < len(lines) and lines[idx].startswith("#!"):
        idx += 1
    if idx < len(lines) and CODING_RE.search(lines[idx]):
        idx += 1
    return idx


def find_triple_docstring_end(lines: List[str], start_idx: int) -> int:
    idx = start_idx
    while idx < len(lines) and (lines[idx].strip() == "" or lines[idx].lstrip().startswith("#")):
        idx += 1
    if idx >= len(lines):
        return start_idx

    stripped = lines[idx].lstrip()
    markers = ('"' * 3, "'" * 3)
    marker = None
    for candidate in markers:
        if stripped.startswith(candidate):
            marker = candidate
            break
    if marker is None:
        return start_idx

    rest = stripped[len(marker):]
    if marker in rest:
        return idx + 1

    j = idx + 1
    while j < len(lines):
        if marker in lines[j]:
            return j + 1
        j += 1
    return start_idx


def reorder_future_imports_if_needed(text: str, newline: str) -> Tuple[str, bool]:
    lines = split_lines_keep(text)
    if not any(is_future_line(line) for line in lines):
        return text, False

    without_future = [line for line in lines if not is_future_line(line)]
    insert_at = skip_preamble(without_future)
    doc_end = find_triple_docstring_end(without_future, insert_at)
    if doc_end > insert_at:
        insert_at = doc_end

    future_block = [FUTURE_LINE + newline]
    if insert_at < len(without_future) and without_future[insert_at].strip() != "":
        future_block.append(newline)

    new_lines = list(without_future)
    if insert_at > 0:
        new_lines[insert_at - 1] = ensure_line_end(strip_line_end(new_lines[insert_at - 1]), newline)
    new_lines[insert_at:insert_at] = future_block
    updated = "".join(new_lines)
    if updated == text:
        return text, False
    return updated, True


def ensure_logging_import(text: str, newline: str) -> Tuple[str, bool]:
    if not LOGGING_GETLOGGER_RE.search(text):
        return text, False
    if LOGGING_IMPORT_RE.search(text):
        return text, False

    lines = split_lines_keep(text)
    future_indices = [i for i, line in enumerate(lines) if is_future_line(line)]
    if future_indices:
        insert_at = max(future_indices) + 1
        while insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1
    else:
        insert_at = skip_preamble(lines)
        doc_end = find_triple_docstring_end(lines, insert_at)
        if doc_end > insert_at:
            insert_at = doc_end

    if insert_at > 0:
        lines[insert_at - 1] = ensure_line_end(strip_line_end(lines[insert_at - 1]), newline)
    lines.insert(insert_at, "import logging" + newline)
    return "".join(lines), True


def repair_python_file(path: Path, dry_run: bool = False) -> dict:
    original, newline = read_text(path)
    text = original
    actions: List[dict] = []

    text, concat_repairs = repair_concatenated_future_lines(text, newline)
    if concat_repairs:
        actions.append({"action": "repair_concatenated_future_lines", "items": concat_repairs})

    text, future_reordered = reorder_future_imports_if_needed(text, newline)
    if future_reordered:
        actions.append({"action": "reorder_future_import"})

    text, logging_added = ensure_logging_import(text, newline)
    if logging_added:
        actions.append({"action": "add_logging_import"})

    changed = text != original
    if changed and not dry_run:
        write_text(path, text, newline)

    return {"file": str(path), "changed": changed, "actions": actions}


def iter_target_files(root: Path) -> List[Path]:
    targets: List[Path] = []
    app_dir = root / "app"
    if app_dir.exists():
        targets.extend(sorted(app_dir.rglob("*.py")))
    for extra in (root / "config.py", root / "wsgi.py", root / "run.py"):
        if extra.exists():
            targets.append(extra)
    return targets


def compile_scan(root: Path) -> List[dict]:
    findings: List[dict] = []
    targets = iter_target_files(root)
    scripts_quality = root / "scripts" / "quality"
    if scripts_quality.exists():
        targets.extend(sorted(scripts_quality.glob("repair_bys360_quality9_future_docstring_syntax_hotfix_v*.py")))
    for path in targets:
        try:
            text, _ = read_text(path)
            compile(text, str(path), "exec")
        except SyntaxError as exc:
            findings.append({"file": str(path), "line": exc.lineno, "error": str(exc)})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="all", choices=["audit", "repair", "all"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not (root / "app").exists():
        print(json.dumps({"package": PACKAGE, "ok": False, "error": f"app klasoru bulunamadi: {root}"}, ensure_ascii=False))
        return 2

    dry_run = args.dry_run or args.mode == "audit"
    changed: List[dict] = []
    checked = 0

    v5_result = retire_broken_v5_script(root, dry_run=dry_run)
    if v5_result["changed"]:
        changed.append(v5_result)

    for path in iter_target_files(root):
        checked += 1
        result = repair_python_file(path, dry_run=dry_run)
        if result["changed"]:
            changed.append(result)

    findings = compile_scan(root)
    payload = {
        "package": PACKAGE,
        "ok": not findings,
        "mode": args.mode,
        "dry_run": dry_run,
        "checked": checked,
        "changed_count": len(changed),
        "changed": changed[:120],
        "finding_count": len(findings),
        "findings": findings[:80],
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
