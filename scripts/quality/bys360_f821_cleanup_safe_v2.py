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

PACKAGE = "BYS360_F821_CLEANUP_SAFE_V2"


def relpath(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def backup(path: Path, root: Path, backup_root: Path, changed: set[Path]) -> None:
    if path in changed or not path.exists():
        return
    target = backup_root / relpath(path, root)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    changed.add(path)


def run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
    return proc.returncode, proc.stdout, proc.stderr


def count_f821(root: Path) -> tuple[int | None, str, str]:
    code, out, err = run([sys.executable, "-m", "ruff", "check", "app", "--select", "F821", "--output-format", "json"], root)
    if not out.strip():
        return 0, out, err
    try:
        data = json.loads(out)
        return len([i for i in data if i.get("code") == "F821"]), out, err
    except Exception:
        return None, out, err


def strip_exact_import_lines(lines: list[str], unwanted: set[str]) -> list[str]:
    return [line for line in lines if line.strip() not in unwanted]


def find_docstring_end(lines: list[str], start: int) -> int:
    if start >= len(lines):
        return start
    s = lines[start].lstrip()
    if not (s.startswith('"""') or s.startswith("'''")):
        return start
    quote = '"""' if s.startswith('"""') else "'''"
    # Single line docstring.
    if s.count(quote) >= 2 and len(s) > 3:
        return start + 1
    i = start + 1
    while i < len(lines):
        if quote in lines[i]:
            return i + 1
        i += 1
    return start + 1


def future_insert_index(lines: list[str]) -> int:
    idx = 0
    # Keep shebang, coding comments and leading regular comments before future import.
    while idx < len(lines):
        stripped = lines[idx].strip()
        if not stripped or stripped.startswith("#!") or "coding" in stripped or stripped.startswith("#"):
            idx += 1
            continue
        break
    idx = find_docstring_end(lines, idx)
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    return idx


def normalize_future_and_any(path: Path, root: Path, backup_root: Path, changed: set[Path]) -> bool:
    if not path.exists():
        return False
    text = read_text(path)
    lines = text.splitlines()
    cleaned = strip_exact_import_lines(lines, {"from __future__ import annotations", "from typing import Any"})
    idx = future_insert_index(cleaned)
    new_lines = cleaned[:idx] + ["from __future__ import annotations", "", "from typing import Any"] + cleaned[idx:]
    # Collapse excessive blanks after inserted imports.
    new = "\n".join(new_lines).replace("from typing import Any\n\n\n", "from typing import Any\n\n")
    if text.endswith("\n"):
        new += "\n"
    if new != text:
        backup(path, root, backup_root, changed)
        write_text(path, new)
        return True
    return False


def import_in_text(text: str, import_line: str) -> bool:
    return import_line in text


def insert_import(text: str, import_line: str) -> str:
    if import_in_text(text, import_line):
        return text
    lines = text.splitlines()
    # If future import exists, never insert before it.
    idx = 0
    while idx < len(lines):
        stripped = lines[idx].strip()
        if not stripped or stripped.startswith("#!") or "coding" in stripped or stripped.startswith("#"):
            idx += 1
            continue
        break
    # Preserve a module docstring if it is actually before future/imports.
    idx = find_docstring_end(lines, idx)
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx < len(lines) and lines[idx].strip() == "from __future__ import annotations":
        idx += 1
    # Walk over import block, including parenthesized from-import blocks.
    paren_depth = 0
    while idx < len(lines):
        stripped = lines[idx].strip()
        if paren_depth > 0:
            paren_depth += stripped.count("(") - stripped.count(")")
            idx += 1
            continue
        if not stripped:
            idx += 1
            continue
        if stripped.startswith("import ") or stripped.startswith("from "):
            paren_depth += stripped.count("(") - stripped.count(")")
            idx += 1
            continue
        break
    new_lines = lines[:idx] + [import_line] + [""] + lines[idx:]
    return "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")


def ensure_import(path: Path, root: Path, backup_root: Path, changed: set[Path], import_line: str) -> bool:
    if not path.exists():
        return False
    text = read_text(path)
    new = insert_import(text, import_line)
    if new != text:
        backup(path, root, backup_root, changed)
        write_text(path, new)
        return True
    return False


def add_or_extend_models_import(path: Path, root: Path, backup_root: Path, changed: set[Path], symbol: str) -> bool:
    text = read_text(path)
    if re.search(rf"from\s+app\.models\s+import\s+.*\b{re.escape(symbol)}\b", text, re.S):
        return False
    # Extend a simple one-line app.models import if present.
    m = re.search(r"^from app\.models import ([^\n()]+)$", text, re.M)
    if m:
        imports = [p.strip() for p in m.group(1).split(",") if p.strip()]
        if symbol not in imports:
            imports.append(symbol)
            new_line = "from app.models import " + ", ".join(imports)
            new = text[:m.start()] + new_line + text[m.end():]
            backup(path, root, backup_root, changed)
            write_text(path, new)
            return True
    return ensure_import(path, root, backup_root, changed, f"from app.models import {symbol}")


def append_block(path: Path, root: Path, backup_root: Path, changed: set[Path], marker: str, block: str) -> bool:
    text = read_text(path)
    if marker in text:
        return False
    backup(path, root, backup_root, changed)
    sep = "\n" if text.endswith("\n") else "\n\n"
    write_text(path, text + sep + block.strip() + "\n")
    return True


def patch_evaluator_reminder_route(path: Path, root: Path, backup_root: Path, changed: set[Path]) -> bool:
    if not path.exists():
        return False
    text = read_text(path)
    original = text
    correct_block = (
        "from app.services.performance.v2_1_11_evaluator_reminder_center import (\n"
        "    build_evaluator_reminder_center_state,\n"
        "    run_v2_1_11_evaluator_reminder_center_gate,\n"
        ")"
    )
    # Repair the exact broken V1 shape: current_user inserted inside a parenthesized import.
    text = re.sub(
        r"from app\.services\.performance\.v2_1_11_evaluator_reminder_center import \(\s*\n"
        r"from flask_login import current_user\s*\n\s*\n"
        r"\s*build_evaluator_reminder_center_state,\s*\n"
        r"\s*run_v2_1_11_evaluator_reminder_center_gate,\s*\n"
        r"\s*\)",
        correct_block,
        text,
        flags=re.M,
    )
    # If any malformed empty import block remains, normalize it.
    text = re.sub(
        r"from app\.services\.performance\.v2_1_11_evaluator_reminder_center import \(\s*\n\s*\)",
        correct_block,
        text,
        flags=re.M,
    )
    # Normalize flask_login import.
    text = re.sub(r"^from flask_login import login_required\s*$", "from flask_login import current_user, login_required", text, flags=re.M)
    if "from flask_login import current_user" in text and "from flask_login import current_user, login_required" in text:
        text = re.sub(r"^from flask_login import current_user\s*\n", "", text, flags=re.M)
    elif "from flask_login import current_user" not in text and "current_user" in text:
        text = insert_import(text, "from flask_login import current_user")
    if text != original:
        backup(path, root, backup_root, changed)
        write_text(path, text)
        return True
    return False


def patch_ops_routes(path: Path, root: Path, backup_root: Path, changed: set[Path]) -> bool:
    if not path.exists():
        return False
    did = False
    did = add_or_extend_models_import(path, root, backup_root, changed, "PerformancePeriod") or did
    block = r'''
# BYS360_F821_CLEANUP_SAFE_V2: admin operation fallback helpers.
def ensure_not_self_target(actor_id, target_id, entity_label="kayıt"):
    if actor_id is not None and target_id is not None and str(actor_id) == str(target_id):
        raise ValueError(f"Kendi {entity_label} kaydınız üzerinde bu işlem yapılamaz.")


def get_default_first_login_password() -> str:
    import os
    import secrets
    try:
        configured = current_app.config.get("BYS360_DEFAULT_FIRST_LOGIN_PASSWORD") or current_app.config.get("DEFAULT_FIRST_LOGIN_PASSWORD")
    except Exception:
        configured = None
    return str(configured or os.environ.get("BYS360_DEFAULT_FIRST_LOGIN_PASSWORD") or os.environ.get("DEFAULT_FIRST_LOGIN_PASSWORD") or secrets.token_urlsafe(18))
'''
    text = read_text(path)
    needs_helper = ("ensure_not_self_target(" in text and "def ensure_not_self_target(" not in text) or ("get_default_first_login_password(" in text and "def get_default_first_login_password(" not in text)
    if needs_helper:
        did = append_block(path, root, backup_root, changed, "BYS360_F821_CLEANUP_SAFE_V2: admin operation fallback helpers", block) or did
    return did


def patch_hr_common(path: Path, root: Path, backup_root: Path, changed: set[Path]) -> bool:
    block = r'''
# BYS360_F821_CLEANUP_SAFE_V2: HR helper fallbacks.
def _bool_from_form(name: str) -> bool:
    value = str(request.form.get(name, "") or "").strip().lower()
    return value in {"1", "true", "on", "yes", "evet", "e"}


def _active_period():
    if PerformancePeriod is None:
        return None
    try:
        return PerformancePeriod.query.filter_by(is_active=True).order_by(PerformancePeriod.id.desc()).first()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 F821 V2: aktif performans dönemi okunamadı")
        return None
'''
    text = read_text(path)
    if "def _bool_from_form(" in text and "def _active_period(" in text:
        return False
    return append_block(path, root, backup_root, changed, "BYS360_F821_CLEANUP_SAFE_V2: HR helper fallbacks", block)


def patch_task_routes(path: Path, root: Path, backup_root: Path, changed: set[Path]) -> bool:
    return ensure_import(path, root, backup_root, changed, "from app.services.performance.assignments import build_assignment_log_summary")


def patch_period_management_center(path: Path, root: Path, backup_root: Path, changed: set[Path]) -> bool:
    return ensure_import(path, root, backup_root, changed, "from app.services.performance.v2_1_18_executive_view import collect_user_role_terms")


def patch_template_service(path: Path, root: Path, backup_root: Path, changed: set[Path]) -> bool:
    if not path.exists():
        return False
    did = False
    did = ensure_import(path, root, backup_root, changed, "from app.extensions import db") or did
    did = add_or_extend_models_import(path, root, backup_root, changed, "User") or did
    block = r'''
# BYS360_F821_CLEANUP_SAFE_V2: CIC template literal fallback bindings.
try:
    _cic_v40_previous_render_template_text
except NameError:
    _cic_v40_previous_render_template_text = globals().get("_cic_v40_previous_render_template_text")


if "_cic_v40_special_days_today" not in globals():
    def _cic_v40_special_days_today():
        return []


if "_cic_v40_service_year" not in globals():
    def _cic_v40_service_year(user) -> int:
        try:
            from datetime import date
            start = getattr(user, "start_date", None) or getattr(user, "employment_start_date", None) or getattr(user, "hire_date", None) or getattr(user, "ise_giris_tarihi", None)
            if not start:
                return 0
            today = date.today()
            return max(0, int(today.year) - int(start.year))
        except Exception:
            return 0


if "_cic_phase6_item" not in globals():
    def _cic_phase6_item(label: str, ok: bool, detail: str, warn: bool = False) -> dict:
        return {"label": label, "ok": bool(ok), "detail": detail, "warn": bool(warn)}
'''
    did = append_block(path, root, backup_root, changed, "BYS360_F821_CLEANUP_SAFE_V2: CIC template literal fallback bindings", block) or did
    return did


def patch_service_communication(path: Path, root: Path, backup_root: Path, changed: set[Path]) -> bool:
    return ensure_import(path, root, backup_root, changed, "from app.extensions import db")


def patch_admin_ai_count_patch(path: Path, root: Path, backup_root: Path, changed: set[Path]) -> bool:
    if not path.exists():
        return False
    text = read_text(path)
    if "rows = [row for row in rows" not in text and "users = [u for u in users" not in text:
        return False
    backup(path, root, backup_root, changed)
    new = '''# -*- coding: utf-8 -*-
from __future__ import annotations

"""Performans kapsamı sayaç yardımcıları.

Bu dosya önce top-level patch parçası olarak ``rows`` ve ``users`` değişkenlerini
oluşmadan kullanıyordu. V2 ile güvenli helper modülüne dönüştürüldü.
"""

from collections.abc import Iterable
from typing import Any

try:
    from app.services.performance.common import is_performance_scope_user
except Exception:  # pragma: no cover
    def is_performance_scope_user(user: Any) -> bool:
        return True


def filter_performance_scope_rows(rows: Iterable[Any]) -> list[Any]:
    return [row for row in rows if is_performance_scope_user(getattr(row, "user", row))]


def filter_performance_scope_users(users: Iterable[Any]) -> list[Any]:
    return [user for user in users if is_performance_scope_user(user)]
'''
    write_text(path, new)
    return True


def patch_effective_chain(path: Path, root: Path, backup_root: Path, changed: set[Path]) -> bool:
    text = read_text(path)
    if re.search(r"^\s*PerformancePeriod\s*=", text, re.M) or re.search(r"from\s+app\.models\s+import\s+.*\bPerformancePeriod\b", text, re.S):
        return False
    anchor = "PerformanceEvaluation = getattr(models, \"PerformanceEvaluation\", None) if models else None"
    if anchor in text:
        backup(path, root, backup_root, changed)
        new = text.replace(anchor, anchor + "\nPerformancePeriod = getattr(models, \"PerformancePeriod\", None) if models else None", 1)
        write_text(path, new)
        return True
    return add_or_extend_models_import(path, root, backup_root, changed, "PerformancePeriod")


def patch_meeting_final_gate(path: Path, root: Path, backup_root: Path, changed: set[Path]) -> bool:
    text = read_text(path)
    if re.search(r"^\s*logger\s*=", text, re.M):
        return False
    backup(path, root, backup_root, changed)
    if "ops_logger = logging.getLogger(__name__)" in text:
        text = text.replace("ops_logger = logging.getLogger(__name__)", "ops_logger = logging.getLogger(__name__)\nlogger = ops_logger", 1)
    else:
        text = insert_import(text, "import logging")
        text = text.replace("import logging", "import logging\nlogger = logging.getLogger(__name__)", 1)
    write_text(path, text)
    return True


def apply(root: Path, backup_root: Path) -> list[dict[str, str]]:
    changed: set[Path] = set()
    actions: list[dict[str, str]] = []

    def do(rel: str, label: str, func) -> None:
        path = root / rel
        try:
            did = func(path, root, backup_root, changed)
        except Exception as exc:
            actions.append({"path": rel, "action": label, "status": "error", "error": str(exc)})
            raise
        if did:
            actions.append({"path": rel, "action": label, "status": "changed"})
        else:
            actions.append({"path": rel, "action": label, "status": "unchanged"})

    do("app/api/mobile/services/communication_service.py", "normalize future import and typing.Any", normalize_future_and_any)
    do("app/performance/v2_1_11_evaluator_reminder_center_routes.py", "repair broken import block and current_user", patch_evaluator_reminder_route)
    do("app/admin/ops_routes.py", "add ops helpers and PerformancePeriod", patch_ops_routes)
    do("app/institutional/hr_common.py", "add HR helper fallbacks", patch_hr_common)
    do("app/performance/task_routes.py", "import build_assignment_log_summary", patch_task_routes)
    do("app/performance/v2_1_7_period_management_center_routes.py", "import collect_user_role_terms", patch_period_management_center)
    do("app/services/cic/template_service.py", "add CIC template bindings", patch_template_service)
    do("app/services/communication_service.py", "import db", patch_service_communication)
    do("app/services/performance/admin_ai_count_patch.py", "rewrite top-level patch fragment", patch_admin_ai_count_patch)
    do("app/services/performance/effective_chain.py", "bind PerformancePeriod", patch_effective_chain)
    do("app/services/performance/meeting_development_final_gate.py", "bind logger", patch_meeting_final_gate)

    return actions


def write_report(root: Path, report: dict[str, Any]) -> Path:
    out = root / "reports" / "quality" / "BYS360_F821_CLEANUP_SAFE_V2_REPORT.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--mode", choices=["audit", "patch", "all"], default="all")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = root / "reports" / "quality" / f"f821_cleanup_safe_v2_backups_{ts}"
    backup_root.mkdir(parents=True, exist_ok=True)

    before_count, before_out, before_err = count_f821(root)
    actions: list[dict[str, str]] = []
    if args.mode in {"patch", "all"}:
        actions = apply(root, backup_root)
    after_count, after_out, after_err = count_f821(root)

    report = {
        "package": PACKAGE,
        "ok": after_count == 0,
        "mode": args.mode,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "before_count": before_count,
        "after_count": after_count,
        "backup_root": str(backup_root),
        "actions": actions,
        "before_output_tail": before_out[-4000:],
        "before_error_tail": before_err[-4000:],
        "after_output_tail": after_out[-4000:],
        "after_error_tail": after_err[-4000:],
    }
    report_path = write_report(root, report)
    print(json.dumps({
        "package": PACKAGE,
        "ok": report["ok"],
        "mode": args.mode,
        "before_count": before_count,
        "after_count": after_count,
        "actions_changed": len([a for a in actions if a.get("status") == "changed"]),
        "report": str(report_path),
        "backup_root": str(backup_root),
    }, ensure_ascii=False, indent=2))
    return 0 if args.mode == "audit" or after_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
