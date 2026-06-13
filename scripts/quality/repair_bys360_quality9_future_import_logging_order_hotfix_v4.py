from __future__ import annotations

import argparse
import json
import re
import sys
import tokenize
from io import StringIO
from pathlib import Path
from typing import List, Tuple

PACKAGE = "BYS360_QUALITY9_FUTURE_IMPORT_LOGGING_ORDER_HOTFIX_V4"
FUTURE_LINE = "from __future__ import annotations"
CODING_RE = re.compile(r"coding[:=]\s*[-\w.]+")


def read_text(path: Path) -> Tuple[str, str]:
    raw = path.read_bytes()
    newline = "\r\n" if b"\r\n" in raw[:4096] else "\n"
    try:
        return raw.decode("utf-8-sig"), newline
    except UnicodeDecodeError:
        return raw.decode("cp1254", errors="replace"), newline


def write_text(path: Path, text: str, newline: str) -> None:
    # Keep normal UTF-8 without BOM. Preserve CRLF when the file already used it.
    if newline == "\r\n":
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    path.write_bytes(text.encode("utf-8"))


def split_lines(text: str) -> List[str]:
    lines = text.splitlines(True)
    if not lines:
        return []
    return lines


def line_is_future(line: str) -> bool:
    return line.strip() == FUTURE_LINE


def insertion_index_after_docstring_or_header(lines: List[str]) -> int:
    """Return 0-based insertion index for __future__ imports.

    Python allows module docstring, comments, blank lines, shebang and coding comments
    before from __future__ imports. Ordinary imports/code must come after them.
    """
    if not lines:
        return 0

    # First, detect a true module docstring using tokenize.
    try:
        tokens = tokenize.generate_tokens(StringIO("".join(lines)).readline)
        first_meaningful = None
        for tok in tokens:
            if tok.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.ENCODING):
                continue
            if tok.type in (tokenize.INDENT, tokenize.DEDENT):
                continue
            if tok.type == tokenize.ENDMARKER:
                break
            first_meaningful = tok
            break
        if first_meaningful is not None and first_meaningful.type == tokenize.STRING and first_meaningful.start[1] == 0:
            # Insert right after the module docstring physical end line.
            return first_meaningful.end[0]
    except tokenize.TokenError:
        # Fall back to conservative header detection.
        pass

    idx = 0
    if idx < len(lines) and lines[idx].startswith("#!"):
        idx += 1

    # Encoding comments are only recognized by Python on line 1 or 2.
    for _ in range(2):
        if idx < len(lines) and CODING_RE.search(lines[idx]):
            idx += 1
        elif idx < len(lines) and lines[idx].strip() == "":
            # A blank line before a second-line encoding comment is allowed in practice.
            idx += 1
        else:
            break

    # Keep leading comments/blanks above the future import if they were already a header.
    # Stop before the first ordinary import or code line.
    while idx < len(lines):
        stripped = lines[idx].strip()
        if stripped == "" or stripped.startswith("#"):
            idx += 1
            continue
        break
    return idx


def normalize_future_import_order(path: Path, dry_run: bool = False) -> dict:
    original, newline = read_text(path)
    lines = split_lines(original)
    if not lines:
        return {"file": str(path), "changed": False, "status": "empty"}

    future_count = sum(1 for line in lines if line_is_future(line))
    if future_count == 0:
        return {"file": str(path), "changed": False, "status": "no_future_import"}

    # Remove all duplicate/misplaced future annotations first.
    without_future = [line for line in lines if not line_is_future(line)]
    insert_at = insertion_index_after_docstring_or_header(without_future)

    # Avoid extra blank churn: add a blank line after the future import if next line is ordinary import/code.
    future_line = FUTURE_LINE + ("\r\n" if newline == "\r\n" else "\n")
    new_lines = without_future[:insert_at] + [future_line] + without_future[insert_at:]

    # Ensure a single blank line between future import and a following non-blank ordinary import/code.
    idx = insert_at + 1
    if idx < len(new_lines):
        next_stripped = new_lines[idx].strip()
        if next_stripped and not next_stripped.startswith("#"):
            new_lines.insert(idx, "\n")

    updated = "".join(new_lines)
    changed = updated != original
    if changed and not dry_run:
        write_text(path, updated, newline)

    return {
        "file": str(path),
        "changed": changed,
        "status": "future_import_reordered" if changed else "already_ok",
        "future_count_before": future_count,
    }


def scan_future_import_violations(root: Path) -> List[dict]:
    violations: List[dict] = []
    for path in sorted((root / "app").rglob("*.py")):
        text, _ = read_text(path)
        lines = split_lines(text)
        if not any(line_is_future(line) for line in lines):
            continue
        # Try compiling the single file because Python gives exact future ordering failures.
        try:
            compile(text, str(path), "exec")
        except SyntaxError as exc:
            if "from __future__ imports must occur" in str(exc):
                violations.append({"file": str(path), "line": exc.lineno, "error": str(exc)})
    return violations


def ensure_logging_import_position(root: Path, dry_run: bool = False) -> List[dict]:
    """Fix only files that use logging.getLogger without importing logging.

    Insert import logging after future imports when present, never above them.
    """
    changed: List[dict] = []
    for path in sorted((root / "app").rglob("*.py")):
        text, newline = read_text(path)
        if "logging.getLogger" not in text:
            continue
        if re.search(r"^\s*import\s+logging\b", text, flags=re.M) or re.search(r"^\s*from\s+logging\s+import\s+", text, flags=re.M):
            continue
        lines = split_lines(text)
        # If a future import exists, place logging right after the future import block and following blank.
        future_indices = [i for i, line in enumerate(lines) if line_is_future(line)]
        if future_indices:
            insert_at = max(future_indices) + 1
            while insert_at < len(lines) and lines[insert_at].strip() == "":
                insert_at += 1
        else:
            insert_at = insertion_index_after_docstring_or_header(lines)
        import_line = "import logging" + ("\r\n" if newline == "\r\n" else "\n")
        lines.insert(insert_at, import_line)
        updated = "".join(lines)
        if not dry_run:
            write_text(path, updated, newline)
        changed.append({"file": str(path), "status": "added_import_logging"})
    return changed


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
    results: List[dict] = []
    logging_changes: List[dict] = []

    if args.mode in {"repair", "all", "audit"}:
        for path in sorted((root / "app").rglob("*.py")):
            try:
                result = normalize_future_import_order(path, dry_run=dry_run)
                if result.get("changed") or result.get("status") not in {"no_future_import", "empty", "already_ok"}:
                    results.append(result)
            except Exception as exc:
                results.append({"file": str(path), "changed": False, "status": "error", "error": str(exc)})
        if not dry_run:
            logging_changes = ensure_logging_import_position(root, dry_run=False)
            # A logging import added after future reordering could still be fine, but normalize again just in case.
            for path in sorted((root / "app").rglob("*.py")):
                normalize_future_import_order(path, dry_run=False)

    violations = scan_future_import_violations(root)
    findings = [r for r in results if r.get("status") == "error"] + violations
    ok = not findings
    changed = [r for r in results if r.get("changed")]

    payload = {
        "package": PACKAGE,
        "ok": ok,
        "mode": args.mode,
        "dry_run": dry_run,
        "changed_count": len(changed) + len(logging_changes),
        "changed": changed[:200],
        "logging_changes": logging_changes[:200],
        "finding_count": len(findings),
        "findings": findings[:200],
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
