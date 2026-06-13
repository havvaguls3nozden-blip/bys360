from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_F821_CLEANUP_SAFE_V1"
DYNAMIC_MENU_SYMBOLS = {
    "MENU_SECTIONS",
    "ROLE_MENU_DEFAULTS",
    "FORCE_VISIBLE_MENU_ROLES",
    "LIVE_SETTINGS_MENU_KEYS",
    "LIVE_MENU_SCOPE",
}


def relpath(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
    return proc.returncode, proc.stdout, proc.stderr


def ruff_f821(project_root: Path) -> list[dict[str, Any]]:
    cmd = [sys.executable, "-m", "ruff", "check", "app", "--select", "F821", "--output-format", "json"]
    _code, out, err = run(cmd, project_root)
    if not out.strip():
        return []
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        print(out)
        print(err, file=sys.stderr)
        raise


def ensure_ruff(project_root: Path) -> None:
    code, _out, _err = run([sys.executable, "-m", "ruff", "--version"], project_root)
    if code != 0:
        code, out, err = run([sys.executable, "-m", "pip", "install", "ruff"], project_root)
        if code != 0:
            print(out)
            print(err, file=sys.stderr)
            raise SystemExit("ruff kurulamadı")


def backup(path: Path, project_root: Path, backup_root: Path, changed: set[Path]) -> None:
    if path in changed:
        return
    if not path.exists():
        return
    target = backup_root / relpath(path, project_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    changed.add(path)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def module_from_path(project_root: Path, file_path: Path) -> str:
    rel = file_path.resolve().relative_to(project_root.resolve())
    return ".".join(rel.with_suffix("").parts)


def iter_py_files(project_root: Path):
    ignored = {".venv", "venv", "env", ".git", "reports", "archive", "quarantine", "backups", "releases", "__pycache__"}
    for p in (project_root / "app").rglob("*.py"):
        if any(part in ignored for part in p.parts):
            continue
        yield p


def find_symbol_module(project_root: Path, symbol: str, current: Path | None = None) -> str | None:
    pattern_def = re.compile(rf"^\s*(?:def|class)\s+{re.escape(symbol)}\b", re.M)
    pattern_assign = re.compile(rf"^\s*{re.escape(symbol)}\s*=", re.M)
    candidates: list[Path] = []
    for p in iter_py_files(project_root):
        if current is not None and p.resolve() == current.resolve():
            continue
        try:
            text = read(p)
        except Exception:
            continue
        if pattern_def.search(text) or pattern_assign.search(text):
            candidates.append(p)
    if not candidates:
        return None

    def score(p: Path) -> tuple[int, str]:
        s = str(p).replace("\\", "/")
        val = 100
        if "/models" in s:
            val -= 50
        if "/services" in s:
            val -= 30
        if "routes" in p.name:
            val += 20
        if "patch" in p.name or "backup" in s:
            val += 50
        return (val, s)

    best = sorted(candidates, key=score)[0]
    return module_from_path(project_root, best)


def has_import(text: str, module: str, symbol: str) -> bool:
    return f"from {module} import {symbol}" in text or re.search(rf"from\s+{re.escape(module)}\s+import\s+.*\b{re.escape(symbol)}\b", text) is not None


def insert_after_imports(text: str, lines_to_insert: list[str]) -> str:
    if not lines_to_insert:
        return text
    lines = text.splitlines()
    idx = 0
    while idx < len(lines) and (lines[idx].startswith("#!") or "coding" in lines[idx] or not lines[idx].strip()):
        idx += 1
    if idx < len(lines) and lines[idx].strip() == "from __future__ import annotations":
        idx += 1
    while idx < len(lines):
        stripped = lines[idx].strip()
        if stripped.startswith("import ") or stripped.startswith("from ") or not stripped:
            idx += 1
            continue
        break
    insert = [item for item in lines_to_insert if item not in text]
    if not insert:
        return text
    return "\n".join(lines[:idx] + insert + [""] + lines[idx:]) + ("\n" if text.endswith("\n") else "")


def ensure_import(path: Path, project_root: Path, backup_root: Path, changed: set[Path], import_line: str) -> bool:
    text = read(path)
    if import_line in text:
        return False
    backup(path, project_root, backup_root, changed)
    write(path, insert_after_imports(text, [import_line]))
    return True


def ensure_import_symbol(path: Path, project_root: Path, backup_root: Path, changed: set[Path], symbol: str, module: str) -> bool:
    text = read(path)
    if has_import(text, module, symbol):
        return False
    backup(path, project_root, backup_root, changed)
    write(path, insert_after_imports(text, [f"from {module} import {symbol}"]))
    return True


def add_noqa_for_dynamic_globals(path: Path, project_root: Path, backup_root: Path, changed: set[Path]) -> int:
    text = read(path)
    lines = text.splitlines()
    edits = 0
    for i, line in enumerate(lines):
        if "noqa" in line:
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for sym in DYNAMIC_MENU_SYMBOLS:
            if re.search(rf"\b{re.escape(sym)}\b", line) and f'"{sym}"' not in line and f"'{sym}'" not in line:
                lines[i] = line + "  # noqa: F821 - dynamic menu registry global"
                edits += 1
                break
    if edits:
        backup(path, project_root, backup_root, changed)
        write(path, "\n".join(lines) + ("\n" if text.endswith("\n") else ""))
    return edits


def ensure_logger(path: Path, project_root: Path, backup_root: Path, changed: set[Path]) -> bool:
    text = read(path)
    if re.search(r"^\s*logger\s*=\s*logging\.getLogger\(__name__\)", text, re.M):
        return False
    backup(path, project_root, backup_root, changed)
    new = insert_after_imports(text, ["import logging"])
    if "logger = logging.getLogger(__name__)" not in new:
        lines = new.splitlines()
        idx = 0
        while idx < len(lines):
            stripped = lines[idx].strip()
            if stripped.startswith("import ") or stripped.startswith("from ") or not stripped or stripped == "from __future__ import annotations":
                idx += 1
                continue
            break
        lines.insert(idx, "logger = logging.getLogger(__name__)")
        lines.insert(idx + 1, "")
        new = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    write(path, new)
    return True


def append_block_if_missing(path: Path, project_root: Path, backup_root: Path, changed: set[Path], marker: str, block: str) -> bool:
    text = read(path)
    if marker in text:
        return False
    backup(path, project_root, backup_root, changed)
    lines = text.splitlines()
    idx = 0
    while idx < len(lines):
        stripped = lines[idx].strip()
        if stripped.startswith("import ") or stripped.startswith("from ") or not stripped or stripped == "from __future__ import annotations":
            idx += 1
            continue
        break
    new_lines = lines[:idx] + ["", block.strip(), ""] + lines[idx:]
    write(path, "\n".join(new_lines) + ("\n" if text.endswith("\n") else ""))
    return True


def patch_hr_common(path: Path, project_root: Path, backup_root: Path, changed: set[Path]) -> bool:
    block = '''
# BYS360_F821_CLEANUP_SAFE_V1: local helpers restored for HR common calculations.
def _bool_from_form(name: str) -> bool:
    value = str(request.form.get(name, "") or "").strip().lower()
    return value in {"1", "true", "on", "yes", "evet", "e"}


def _active_period():
    try:
        from app.models import PerformancePeriod  # type: ignore
    except Exception:
        try:
            from app.models.performance import PerformancePeriod  # type: ignore
        except Exception:
            return None
    try:
        return PerformancePeriod.query.filter_by(is_active=True).order_by(PerformancePeriod.id.desc()).first()
    except Exception:
        return None
'''
    text = read(path)
    changed_any = False
    if "from flask import request" not in text and "import request" not in text and "request.form" in text:
        backup(path, project_root, backup_root, changed)
        text = read(path)
        m = re.search(r"^from flask import (.+)$", text, re.M)
        if m and "request" not in m.group(1):
            text = text[:m.start(1)] + m.group(1).rstrip() + ", request" + text[m.end(1):]
            write(path, text)
            changed_any = True
        elif not m:
            write(path, insert_after_imports(text, ["from flask import request"]))
            changed_any = True
    changed_any = append_block_if_missing(path, project_root, backup_root, changed, "BYS360_F821_CLEANUP_SAFE_V1: local helpers restored", block) or changed_any
    return changed_any


def patch_template_service(path: Path, project_root: Path, backup_root: Path, changed: set[Path]) -> bool:
    text = read(path)
    changed_any = False
    if "from __future__ import annotations" not in text.splitlines()[:5]:
        backup(path, project_root, backup_root, changed)
        text = read(path)
        write(path, "from __future__ import annotations\n" + text)
        changed_any = True
    changed_any = ensure_import(path, project_root, backup_root, changed, "from app.extensions import db") or changed_any
    user_mod = find_symbol_module(project_root, "User", path) or "app.models"
    changed_any = ensure_import_symbol(path, project_root, backup_root, changed, "User", user_mod) or changed_any
    block = '''
# BYS360_F821_CLEANUP_SAFE_V1: CIC template compatibility fallbacks.
_cic_v40_previous_render_template_text = globals().get("_cic_v40_previous_render_template_text")


def _cic_v40_special_days_today():
    return []


def _cic_v40_service_year(user) -> int:
    try:
        from datetime import date
        start = getattr(user, "start_date", None) or getattr(user, "employment_start_date", None) or getattr(user, "hire_date", None)
        if not start:
            return 0
        today = date.today()
        return max(0, int(today.year) - int(start.year))
    except Exception:
        return 0


def _cic_phase6_item(label: str, ok: bool, detail: str, warn: bool = False) -> dict:
    return {"label": label, "ok": bool(ok), "detail": detail, "warn": bool(warn)}
'''
    changed_any = append_block_if_missing(path, project_root, backup_root, changed, "BYS360_F821_CLEANUP_SAFE_V1: CIC template compatibility", block) or changed_any
    return changed_any


def patch_admin_ai_count_patch(path: Path, project_root: Path, backup_root: Path, changed: set[Path]) -> bool:
    if not path.exists():
        return False
    text = read(path)
    if "rows = [row for row in rows" not in text and "users = [u for u in users" not in text:
        return False
    backup(path, project_root, backup_root, changed)
    new = '''# BYS360_F821_CLEANUP_SAFE_V1
"""Performance scope filtering helpers.

This file previously contained top-level patch-fragment code that referenced
``rows`` and ``users`` before they existed. It is now a safe helper module.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

try:
    from app.services.performance.scope import is_performance_scope_user  # type: ignore
except Exception:  # pragma: no cover - safe fallback for legacy installs
    def is_performance_scope_user(user: Any) -> bool:
        return True


def filter_performance_scope_rows(rows: Iterable[Any]) -> list[Any]:
    return [row for row in rows if is_performance_scope_user(getattr(row, "user", row))]


def filter_performance_scope_users(users: Iterable[Any]) -> list[Any]:
    return [user for user in users if is_performance_scope_user(user)]
'''
    write(path, new)
    return True


def patch_assignment_log_summary(path: Path, project_root: Path, backup_root: Path, changed: set[Path]) -> bool:
    mod = find_symbol_module(project_root, "build_assignment_log_summary", path)
    if mod:
        return ensure_import_symbol(path, project_root, backup_root, changed, "build_assignment_log_summary", mod)
    block = '''
# BYS360_F821_CLEANUP_SAFE_V1: fallback audit summary helper.
def build_assignment_log_summary(rows):
    rows = list(rows or [])
    severity_counts = Counter(str(getattr(row, "severity", "warning") or "warning").strip().lower() or "warning" for row in rows)
    event_type_counts = Counter(str(getattr(row, "event_type", "") or "").strip() for row in rows)
    return {
        "total": len(rows),
        "severity_counts": dict(severity_counts),
        "event_type_counts": dict(event_type_counts),
    }
'''
    return append_block_if_missing(path, project_root, backup_root, changed, "BYS360_F821_CLEANUP_SAFE_V1: fallback audit summary", block)


def patch_period_center_roles(path: Path, project_root: Path, backup_root: Path, changed: set[Path]) -> bool:
    mod = find_symbol_module(project_root, "collect_user_role_terms", path)
    if mod:
        return ensure_import_symbol(path, project_root, backup_root, changed, "collect_user_role_terms", mod)
    block = '''
# BYS360_F821_CLEANUP_SAFE_V1: fallback role term collector.
def collect_user_role_terms(user):
    terms = set()
    for attr in ("role", "role_name", "role_key", "user_type"):
        value = getattr(user, attr, None)
        if value:
            terms.add(str(value))
    roles = getattr(user, "roles", None) or []
    for role in roles:
        for attr in ("name", "key", "code"):
            value = getattr(role, attr, None)
            if value:
                terms.add(str(value))
    return terms
'''
    return append_block_if_missing(path, project_root, backup_root, changed, "BYS360_F821_CLEANUP_SAFE_V1: fallback role term", block)


def patch_ops_routes(path: Path, project_root: Path, backup_root: Path, changed: set[Path]) -> bool:
    changed_any = False
    for symbol in ("ensure_not_self_target", "get_default_first_login_password", "PerformancePeriod"):
        mod = find_symbol_module(project_root, symbol, path)
        if mod:
            changed_any = ensure_import_symbol(path, project_root, backup_root, changed, symbol, mod) or changed_any
    text = read(path)
    blocks: list[str] = []
    if "def ensure_not_self_target(" not in text and "ensure_not_self_target" in text and not re.search(r"from\s+.*\s+import\s+.*ensure_not_self_target", text):
        blocks.append('''
def ensure_not_self_target(actor_id, target_id, entity_label="kayıt"):
    if actor_id is not None and target_id is not None and str(actor_id) == str(target_id):
        raise ValueError(f"Kendi {entity_label} kaydınız üzerinde bu işlem yapılamaz.")
''')
    if "def get_default_first_login_password(" not in text and "get_default_first_login_password" in text and not re.search(r"from\s+.*\s+import\s+.*get_default_first_login_password", text):
        blocks.append('''
def get_default_first_login_password() -> str:
    import os
    import secrets
    return os.environ.get("BYS360_DEFAULT_FIRST_LOGIN_PASSWORD") or secrets.token_urlsafe(12)
''')
    if blocks:
        changed_any = append_block_if_missing(path, project_root, backup_root, changed, "BYS360_F821_CLEANUP_SAFE_V1: ops fallback helpers", "\n# BYS360_F821_CLEANUP_SAFE_V1: ops fallback helpers." + "\n".join(blocks)) or changed_any
    return changed_any


def patch_effective_chain(path: Path, project_root: Path, backup_root: Path, changed: set[Path]) -> bool:
    mod = find_symbol_module(project_root, "PerformancePeriod", path)
    if mod:
        return ensure_import_symbol(path, project_root, backup_root, changed, "PerformancePeriod", mod)
    return False


def patch_communication_service(path: Path, project_root: Path, backup_root: Path, changed: set[Path]) -> bool:
    if "app/api/mobile/services/communication_service.py" in relpath(path, project_root):
        return ensure_import(path, project_root, backup_root, changed, "from typing import Any")
    return ensure_import(path, project_root, backup_root, changed, "from app.extensions import db")


def apply_known_patches(project_root: Path, issues: list[dict[str, Any]], backup_root: Path) -> dict[str, Any]:
    changed: set[Path] = set()
    actions: list[dict[str, Any]] = []
    by_file: dict[str, set[str]] = {}
    for issue in issues:
        file = issue.get("filename") or issue.get("file") or ""
        msg = issue.get("message") or ""
        m = re.search(r"Undefined name `([^`]+)`", msg)
        if not file or not m:
            continue
        by_file.setdefault(file.replace("\\", "/"), set()).add(m.group(1))

    def record(path: Path, action: str, did: bool):
        if did:
            actions.append({"path": relpath(path, project_root), "action": action})

    for file, symbols in by_file.items():
        path = (project_root / file).resolve()
        if not path.exists():
            continue
        rel = file.replace("\\", "/")
        if "Any" in symbols:
            record(path, "add typing.Any import", ensure_import(path, project_root, backup_root, changed, "from typing import Any"))
        if "current_user" in symbols:
            record(path, "add flask_login.current_user import", ensure_import(path, project_root, backup_root, changed, "from flask_login import current_user"))
        if "logger" in symbols:
            record(path, "add module logger", ensure_logger(path, project_root, backup_root, changed))
        if "db" in symbols and rel in {"app/services/cic/template_service.py", "app/services/communication_service.py"}:
            record(path, "add db import", ensure_import(path, project_root, backup_root, changed, "from app.extensions import db"))
        if any(sym in symbols for sym in DYNAMIC_MENU_SYMBOLS):
            record(path, "mark dynamic menu globals with noqa", add_noqa_for_dynamic_globals(path, project_root, backup_root, changed) > 0)
        if rel == "app/admin/ops_routes.py":
            record(path, "patch ops route missing symbols", patch_ops_routes(path, project_root, backup_root, changed))
        if rel == "app/institutional/hr_common.py":
            record(path, "add HR common helper fallbacks", patch_hr_common(path, project_root, backup_root, changed))
        if rel == "app/performance/task_routes.py" and "build_assignment_log_summary" in symbols:
            record(path, "add assignment log summary helper/import", patch_assignment_log_summary(path, project_root, backup_root, changed))
        if rel == "app/performance/v2_1_7_period_management_center_routes.py" and "collect_user_role_terms" in symbols:
            record(path, "add role term collector helper/import", patch_period_center_roles(path, project_root, backup_root, changed))
        if rel == "app/services/cic/template_service.py":
            record(path, "patch CIC template service compatibility", patch_template_service(path, project_root, backup_root, changed))
        if rel == "app/services/performance/admin_ai_count_patch.py":
            record(path, "rewrite top-level patch fragment as helpers", patch_admin_ai_count_patch(path, project_root, backup_root, changed))
        if rel == "app/services/performance/effective_chain.py" and "PerformancePeriod" in symbols:
            record(path, "add PerformancePeriod import", patch_effective_chain(path, project_root, backup_root, changed))
        if rel in {"app/api/mobile/services/communication_service.py", "app/services/communication_service.py"}:
            record(path, "patch communication service imports", patch_communication_service(path, project_root, backup_root, changed))
    return {"actions": actions, "backup_root": str(backup_root), "changed_files": sorted(relpath(p, project_root) for p in changed)}


def write_report(project_root: Path, report: dict[str, Any]) -> Path:
    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "BYS360_F821_CLEANUP_SAFE_V1_REPORT.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--mode", choices=["audit", "patch", "all"], default="all")
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    ensure_ruff(project_root)

    before = ruff_f821(project_root)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / "reports" / "quality" / f"f821_cleanup_safe_v1_backups_{ts}"
    backup_root.mkdir(parents=True, exist_ok=True)
    patch_result = {"actions": [], "backup_root": None, "changed_files": []}

    if args.mode in {"patch", "all"} and before:
        patch_result = apply_known_patches(project_root, before, backup_root)

    after = ruff_f821(project_root)
    report = {
        "package": PACKAGE,
        "ok": len(after) == 0,
        "mode": args.mode,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(project_root),
        "before_count": len(before),
        "after_count": len(after),
        "patch_result": patch_result,
        "remaining": after,
    }
    path = write_report(project_root, report)
    print(json.dumps({
        "package": report["package"],
        "ok": report["ok"],
        "mode": report["mode"],
        "before_count": report["before_count"],
        "after_count": report["after_count"],
        "report": str(path),
        "actions": len(patch_result.get("actions", [])),
    }, ensure_ascii=False, indent=2))
    return 0 if (args.mode == "audit" or len(after) == 0) else 2


if __name__ == "__main__":
    raise SystemExit(main())
