from __future__ import annotations

import argparse
import ast
import compileall
import json
import re
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

PACKAGE = "BYS360_OPS_HARDENING_V6C_MAIL_NOTIFICATION_SUPPORT"
TARGET_HINTS = (
    "mail", "email", "smtp", "notification", "notifications", "notify",
    "reminder", "reminders", "scheduler", "scheduled", "cron", "job",
    "support", "ticket", "tickets", "feedback", "message", "messages",
    "communication", "survey", "announcement", "duyuru", "bildirim",
)
SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".mypy_cache", ".pytest_cache",
    "node_modules", "backups", "backup", "archive", "archives", "logs", "reports",
    "instance", "migrations", "alembic", "releases", "dist", "build",
}
EXCEPT_RE = re.compile(r"^(?P<indent>\s*)except\s+Exception(?:\s+as\s+(?P<var>[A-Za-z_][A-Za-z0-9_]*))?\s*:\s*(?:#.*)?$")
BROAD_RE = re.compile(r"^\s*except\s+Exception(?:\s+as\s+[A-Za-z_][A-Za-z0-9_]*)?\s*:")
LOG_MARKERS = ("logger.", "logging.", "current_app.logger", ".exception(", ".error(", ".warning(", "raise")


@dataclass
class Change:
    file: str
    line: int
    action: str
    detail: str


@dataclass
class Candidate:
    file: str
    line: int
    risk: str
    has_logging_or_raise: bool


def is_target_file(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root).as_posix().lower()
    except ValueError:
        return False
    if not rel.endswith(".py"):
        return False
    if set(rel.split("/")) & SKIP_DIRS:
        return False
    if not (rel.startswith("app/") or rel in {"config.py", "run.py", "wsgi.py"}):
        return False
    return any(h in rel for h in TARGET_HINTS)


def iter_py_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.py"):
        try:
            parts = set(p.relative_to(root).parts)
        except ValueError:
            continue
        if parts & SKIP_DIRS:
            continue
        yield p


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def module_insert_index_for_import(tree: ast.Module, lines: list[str]) -> int:
    """Return 0-based line index after module docstring, future imports and import block.

    Uses AST end_lineno so multiline imports are never split. This fixes V6B's
    auth_handlers.py issue where logger was injected inside a parenthesized import.
    """
    insert_after_line = 0
    body = list(tree.body)
    idx = 0
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
        insert_after_line = max(insert_after_line, int(getattr(body[0], "end_lineno", body[0].lineno)))
        idx = 1
    while idx < len(body):
        node = body[idx]
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            insert_after_line = max(insert_after_line, int(getattr(node, "end_lineno", node.lineno)))
            idx += 1
            continue
        break
    # Continue through the first contiguous import block after docstring/future imports.
    while idx < len(body):
        node = body[idx]
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            insert_after_line = max(insert_after_line, int(getattr(node, "end_lineno", node.lineno)))
            idx += 1
            continue
        break
    return min(insert_after_line, len(lines))


def has_module_logger(tree: ast.Module) -> bool:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "logger":
                    return True
    return False


def has_logging_import(tree: ast.Module) -> bool:
    for node in tree.body:
        if isinstance(node, ast.Import):
            if any(alias.name == "logging" for alias in node.names):
                return True
    return False


def ensure_logger_boilerplate(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text, changes
    lines = text.splitlines()
    insert_at = module_insert_index_for_import(tree, lines)
    if not has_logging_import(tree):
        lines.insert(insert_at, "import logging")
        changes.append("import logging eklendi")
        # Reparse after adding import so logger goes after the updated import block.
        tree = ast.parse("\n".join(lines) + "\n")
        insert_at = module_insert_index_for_import(tree, lines)
    if not has_module_logger(tree):
        # Keep one visual blank line after imports.
        if insert_at < len(lines) and lines[insert_at].strip():
            lines.insert(insert_at, "")
            insert_at += 1
        lines.insert(insert_at, "logger = logging.getLogger(__name__)")
        changes.append("module logger eklendi")
    new_text = "\n".join(lines) + ("\n" if text.endswith("\n") or lines else "")
    return new_text, changes


def block_has_logging(lines: list[str], idx: int) -> bool:
    m = EXCEPT_RE.match(lines[idx])
    if not m:
        return True
    base_indent = len(m.group("indent"))
    for j in range(idx + 1, min(len(lines), idx + 12)):
        line = lines[j]
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent <= base_indent:
            break
        if any(marker in line for marker in LOG_MARKERS):
            return True
    return False


def guarded_message(rel: str, line_no: int) -> str:
    safe_rel = rel.replace('"', "'")
    return f'logger.exception("BYS360 V6C guarded exception | file={safe_rel} | line={line_no}")'


def apply_to_file(path: Path, root: Path, apply: bool) -> tuple[list[Candidate], list[Change], bool, str | None]:
    original = read_text(path)
    rel = path.relative_to(root).as_posix()
    candidates: list[Candidate] = []
    changes: list[Change] = []
    changed = False
    skipped_reason: str | None = None

    try:
        ast.parse(original)
    except SyntaxError as exc:
        return candidates, changes, False, f"orijinal syntax hatasi: {exc.lineno}:{exc.msg}"

    lines = original.splitlines()
    for idx, line in enumerate(lines):
        m = EXCEPT_RE.match(line)
        if not m:
            continue
        has_log = block_has_logging(lines, idx)
        candidates.append(Candidate(file=rel, line=idx + 1, risk="P0_MAIL_NOTIFICATION_SUPPORT", has_logging_or_raise=has_log))

    if not apply or not candidates:
        return candidates, changes, changed, skipped_reason

    text_with_boiler, boiler_changes = ensure_logger_boilerplate(original)
    try:
        ast.parse(text_with_boiler)
    except SyntaxError as exc:
        return candidates, changes, False, f"boilerplate syntax riski: {exc.lineno}:{exc.msg}"

    lines2 = text_with_boiler.splitlines()
    insertions: list[tuple[int, str]] = []
    for idx, line in enumerate(lines2):
        m = EXCEPT_RE.match(line)
        if m and not block_has_logging(lines2, idx):
            indent = m.group("indent") + "    "
            insertions.append((idx + 1, indent + guarded_message(rel, idx + 1)))
            changes.append(Change(file=rel, line=idx + 1, action="insert_logger_exception", detail="Sessiz/zayif except Exception bloguna logger.exception eklendi"))

    if not insertions:
        return candidates, [], False, skipped_reason

    for bc in boiler_changes:
        changes.append(Change(file=rel, line=1, action="boilerplate", detail=bc))

    for offset, (insert_at, new_line) in enumerate(insertions):
        lines2.insert(insert_at + offset, new_line)
    new_text = "\n".join(lines2) + "\n"
    try:
        ast.parse(new_text)
    except SyntaxError as exc:
        return candidates, [], False, f"degisiklik syntax riski; dosya atlandi: {exc.lineno}:{exc.msg}"

    if new_text != original:
        backup_dir = root / "backups" / "ops_hardening_v6c_mail_notification_support" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)
        path.write_text(new_text, encoding="utf-8")
        changed = True
    return candidates, changes, changed, skipped_reason


def count_broad_target(root: Path) -> int:
    total = 0
    for p in iter_py_files(root):
        if is_target_file(p, root):
            txt = read_text(p)
            total += sum(1 for line in txt.splitlines() if BROAD_RE.match(line))
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", choices=("audit", "apply", "all"), default="all")
    args = ap.parse_args()
    root = Path(args.project_root).resolve()
    apply = args.mode in {"apply", "all"}

    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    md_path = report_dir / "BYS360_OPS_HARDENING_V6C_MAIL_NOTIFICATION_SUPPORT_REPORT.md"
    json_path = report_dir / "BYS360_OPS_HARDENING_V6C_MAIL_NOTIFICATION_SUPPORT_REPORT.json"

    candidates: list[Candidate] = []
    changes: list[Change] = []
    skipped: list[dict] = []
    files_changed = 0
    target_files = 0

    pre_broad = count_broad_target(root)
    for path in iter_py_files(root):
        if not is_target_file(path, root):
            continue
        target_files += 1
        file_candidates, file_changes, changed, skipped_reason = apply_to_file(path, root, apply=apply)
        candidates.extend(file_candidates)
        changes.extend(file_changes)
        if changed:
            files_changed += 1
        if skipped_reason:
            skipped.append({"file": path.relative_to(root).as_posix(), "reason": skipped_reason})

    compile_ok = compileall.compile_dir(str(root / "app"), quiet=1, force=False) if (root / "app").exists() else True
    post_broad = count_broad_target(root)
    changed_blocks = len([c for c in changes if c.action == "insert_logger_exception"])

    result = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "apply" if apply else "audit",
        "target_files": target_files,
        "files_changed": files_changed,
        "candidate_blocks": len(candidates),
        "changed_blocks": changed_blocks,
        "pre_target_broad_except_exception": pre_broad,
        "post_target_broad_except_exception": post_broad,
        "skipped_files": len(skipped),
        "compile_ok": bool(compile_ok),
        "changes": [asdict(c) for c in changes[:500]],
        "skipped": skipped[:200],
        "candidates_sample": [asdict(c) for c in candidates[:300]],
    }
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [f"# {PACKAGE} Raporu", "", "## Özet"]
    for key in ["mode", "target_files", "files_changed", "candidate_blocks", "changed_blocks", "pre_target_broad_except_exception", "post_target_broad_except_exception", "skipped_files", "compile_ok"]:
        md.append(f"- **{key}:** `{result[key]}`")
    md += ["", "## Değişiklikler"]
    if changes:
        md += ["| Dosya | Satır | İşlem | Detay |", "|---|---:|---|---|"]
        for c in changes[:300]:
            md.append(f"| `{c.file}` | {c.line} | `{c.action}` | {c.detail} |")
    else:
        md.append("Değişiklik yapılmadı.")
    if skipped:
        md += ["", "## Atlanan Dosyalar", "Bu dosyalar syntax riski nedeniyle değiştirilmedi; proje güvenliği için uygulama durdurulmadı.", "", "| Dosya | Sebep |", "|---|---|"]
        for item in skipped[:100]:
            md.append(f"| `{item['file']}` | {item['reason']} |")
    md += ["", "## Not", "V6C geniş `except Exception` ifadelerini daraltmaz; mail, bildirim, zamanlanmış iş, destek/iletişim hattında sessiz/zayıf bloklara izlenebilir log ekler. Riskli dosyaları atlayarak projeyi bozmaz."]
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"BYS360_OPS_V6C_REPORT={md_path}")
    print(f"BYS360_OPS_V6C_JSON={json_path}")
    print(json.dumps({k: result[k] for k in ["package", "mode", "target_files", "files_changed", "candidate_blocks", "changed_blocks", "skipped_files", "compile_ok"]}, ensure_ascii=False))
    return 0 if compile_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
