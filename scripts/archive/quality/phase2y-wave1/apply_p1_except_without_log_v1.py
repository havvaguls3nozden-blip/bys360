from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import py_compile
import shutil
from pathlib import Path
from typing import Any


RULE = "EXCEPT_WITHOUT_LOG"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_findings(data: Any, rule_name: str = RULE) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            level = str(x.get("severity") or x.get("level") or x.get("priority") or x.get("rank") or "").upper()
            rule = str(x.get("rule") or x.get("code") or x.get("type") or x.get("category") or x.get("check") or "")
            path = str(x.get("path") or x.get("file") or x.get("filename") or x.get("rel_path") or x.get("relative_path") or "")
            line = x.get("line") or x.get("line_number") or x.get("lineno") or ""
            message = str(x.get("message") or x.get("detail") or x.get("description") or x.get("reason") or "")

            if level == "P1" and rule == rule_name and path and line:
                try:
                    line_no = int(line)
                except Exception:
                    line_no = 0
                if line_no > 0:
                    found.append({
                        "path": path.replace("\\", "/").lstrip("./"),
                        "line": line_no,
                        "rule": rule,
                        "message": message,
                    })

            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(data)

    seen: set[tuple[str, int, str]] = set()
    out: list[dict[str, Any]] = []
    for item in found:
        key = (item["path"], int(item["line"]), item["rule"])
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def handler_has_log_or_raise(lines: list[str], handler: ast.ExceptHandler) -> bool:
    if not handler.body:
        return False

    start = min([handler.lineno] + [getattr(node, "lineno", handler.lineno) for node in handler.body])
    end = max([getattr(node, "end_lineno", getattr(node, "lineno", handler.lineno)) for node in handler.body] + [handler.lineno])
    block = "\n".join(lines[start - 1:end]).lower()

    markers = (
        "logger.",
        "logging.",
        ".exception(",
        ".error(",
        ".warning(",
        ".warn(",
        ".critical(",
        "current_app.logger",
        "app.logger",
        "raise",
    )
    return any(marker in block for marker in markers)


def find_handler(tree: ast.AST, line_no: int) -> ast.ExceptHandler | None:
    exact: list[ast.ExceptHandler] = []
    nearby: list[ast.ExceptHandler] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.lineno == line_no:
                exact.append(node)
            elif abs(node.lineno - line_no) <= 3:
                nearby.append(node)

    if exact:
        return exact[0]
    if nearby:
        nearby.sort(key=lambda n: abs(n.lineno - line_no))
        return nearby[0]
    return None


def _make_log_line(indent: str, rel: str, line_no: int) -> str:
    return (
        f'{indent}__import__("logging").getLogger(__name__).exception('
        f'"BYS360 kalite denetimi: except bloğu loglandı ({rel}:{line_no})")\n'
    )


def _split_inline_except(raw_line: str) -> tuple[str, str] | None:
    # Converts: "except X: pass" or "except X: return y"
    # into header + inline body.
    if ":" not in raw_line:
        return None
    before, after = raw_line.split(":", 1)
    if not before.lstrip().startswith("except"):
        return None
    header = before.rstrip() + ":\n"
    inline_body = after.strip()
    return header, inline_body


def insert_log_line(text: str, rel: str, line_no: int) -> tuple[str, int] | None:
    lines = text.splitlines(keepends=True)
    plain_lines = text.splitlines()
    tree = ast.parse(text)
    handler = find_handler(tree, line_no)

    if handler is None:
        print(f"EXCEPT_HANDLER_NOT_FOUND path={rel} line={line_no}")
        return None

    if handler_has_log_or_raise(plain_lines, handler):
        print(f"EXCEPT_ALREADY_HAS_LOG_OR_RAISE path={rel} line={handler.lineno}")
        return None

    if not handler.body:
        print(f"EXCEPT_BODY_EMPTY path={rel} line={handler.lineno}")
        return None

    except_line_index = handler.lineno - 1
    first_body_line = handler.body[0].lineno
    except_raw = lines[except_line_index]
    except_indent = except_raw[: len(except_raw) - len(except_raw.lstrip())]

    # Case 1: one-line except, e.g. "except Exception: pass".
    # Old P8 inserted before the except line and caused "expected except/finally block".
    if first_body_line == handler.lineno:
        split = _split_inline_except(except_raw)
        if split is None:
            print(f"INLINE_EXCEPT_SPLIT_FAILED path={rel} line={handler.lineno}")
            return None

        header, inline_body = split
        body_indent = except_indent + "    "
        replacement: list[str] = [header, _make_log_line(body_indent, rel, handler.lineno)]

        if inline_body and inline_body != "pass":
            replacement.append(body_indent + inline_body + "\n")
        elif inline_body == "pass":
            # Keep pass for semantic safety; audit should accept because log now exists.
            replacement.append(body_indent + "pass\n")

        lines[except_line_index: except_line_index + 1] = replacement
        return "".join(lines), handler.lineno

    # Case 2: normal multi-line except. Insert at first body line indent.
    first_body_index = first_body_line - 1
    raw = lines[first_body_index]
    body_indent = raw[: len(raw) - len(raw.lstrip())]

    nearby = "".join(lines[max(0, first_body_index - 3): min(len(lines), first_body_index + 3)])
    if "BYS360 kalite denetimi: except bloğu loglandı" in nearby:
        print(f"EXCEPT_LOG_ALREADY_INSERTED_NEARBY path={rel} line={handler.lineno}")
        return None

    lines.insert(first_body_index, _make_log_line(body_indent, rel, handler.lineno))
    return "".join(lines), handler.lineno


def patch_one(project_root: Path, item: dict[str, Any], dry_run: bool) -> bool:
    rel = item["path"]
    line_no = int(item["line"])
    target = (project_root / rel).resolve()

    if not target.exists():
        print(f"TARGET_NOT_FOUND path={rel}")
        return False

    text = target.read_text(encoding="utf-8", errors="ignore")

    try:
        result = insert_log_line(text, rel, line_no)
    except SyntaxError as exc:
        print(f"TARGET_SYNTAX_ERROR path={rel} error={exc}")
        return False

    if result is None:
        print("BYS360_QUALITY_10_10_P8_1_P1_EXCEPT_LOG_NO_CHANGE")
        return False

    patched_text, selected_line = result

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = project_root / ".quality_backup" / f"p8_1_p1_except_log_{stamp}" / rel

    print(f"selected_target={rel}")
    print(f"selected_except_line={selected_line}")
    print(f"backup_file={backup}")

    if dry_run:
        print("BYS360_QUALITY_10_10_P8_1_P1_EXCEPT_LOG_DRYRUN_OK")
        return True

    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup)
    target.write_text(patched_text, encoding="utf-8", newline="")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as exc:
        shutil.copy2(backup, target)
        print("BYS360_QUALITY_10_10_P8_1_P1_EXCEPT_LOG_ROLLED_BACK")
        raise SystemExit(f"COMPILE_FAIL_RESTORED: {exc}") from exc

    print("BYS360_QUALITY_10_10_P8_1_P1_EXCEPT_LOG_OK")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--target", default="")
    parser.add_argument("--line", type=int, default=0)
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--list-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    report = project_root / "reports" / "quality" / "bys360_quality_10_10_audit_v1_clean.json"

    print("BYS360_QUALITY_10_10_P8_1_P1_EXCEPT_LOG_START")
    print(f"project_root={project_root}")

    if not report.exists():
        raise SystemExit(f"REPORT_NOT_FOUND: {report}")

    items = collect_findings(read_json(report), RULE)

    if args.target:
        target_norm = args.target.replace("\\", "/").lstrip("./")
        items = [item for item in items if item["path"] == target_norm]
    if args.line > 0:
        items = [item for item in items if int(item["line"]) == args.line]

    print(f"p1_except_without_log_found={len(items)}")
    for i, item in enumerate(items[: args.limit], 1):
        print(f"[{i}] path={item['path']} line={item['line']} rule={item['rule']} message={item['message']}")

    if args.list_only:
        print("BYS360_QUALITY_10_10_P8_1_P1_EXCEPT_LOG_LIST_OK")
        return 0

    if not items:
        print("BYS360_QUALITY_10_10_P8_1_P1_EXCEPT_LOG_NO_TARGET")
        return 0

    changed = patch_one(project_root, items[0], args.dry_run)
    if not changed:
        print("BYS360_QUALITY_10_10_P8_1_P1_EXCEPT_LOG_FIRST_TARGET_NO_CHANGE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
