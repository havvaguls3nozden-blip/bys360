from pathlib import Path
from datetime import datetime
import json
import shutil
import subprocess
import os
import re

ROOT = Path(".").resolve()
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

A10P_JSON = Path("reports/quality/BYS360_A10P_COMPAT_WRAPPER_RENAME_PLAN.json")
OUT_JSON = Path("reports/quality/BYS360_A10Q_COMPAT_WRAPPER_RENAME_APPLY_DECISION.json")
OUT_MD = Path("reports/quality/BYS360_A10Q_COMPAT_WRAPPER_RENAME_APPLY_DECISION.md")

BACKUP_ROOT = RELEASES / f"A10Q_COMPAT_WRAPPER_RENAME_BACKUP_{STAMP}"

WRAPPER_MARKER = "A10Q_COMPATIBILITY_WRAPPER"

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))

def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def run_cmd(cmd, timeout=1200):
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="ignore",
        env={
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS": "1",
        },
        timeout=timeout,
    )
    return {
        "cmd": " ".join(map(str, cmd)),
        "returncode": proc.returncode,
        "combined": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-12000:],
    }

def parse_pytest_summary(text: str):
    summary = {}
    for num, key in re.findall(r"(\d+)\s+(failed|passed|error|errors|skipped|deselected|warnings|warning)", text or ""):
        key = key.lower()
        if key == "error":
            key = "errors"
        if key == "warning":
            key = "warnings"
        summary[key] = int(num)
    return summary

def module_name_from_path(rel_path: str):
    if not rel_path.endswith(".py"):
        return None
    return rel_path[:-3].replace("/", ".").replace("\\", ".")

def make_wrapper_content(old_rel: str, new_rel: str):
    old_path = Path(old_rel)
    new_path = Path(new_rel)

    if old_path.parent != new_path.parent:
        return None

    new_stem = new_path.stem

    return f'''# -*- coding: utf-8 -*-
"""
{WRAPPER_MARKER}

Bu dosya BYS360 A10Q teknik borç temizliği kapsamında bilerek korunmuştur.
Eski import yolunu kırmamak için yeni modüle yönlendiren compatibility wrapper'dır.

Yeni gerçek modül:
{new_rel}
"""

from .{new_stem} import *  # noqa: F401,F403
'''

def apply_wrapper_rename(item):
    old_rel = item.get("old_path") or item.get("path")
    new_rel = item.get("new_path") or item.get("suggested_new_path")

    if not old_rel or not new_rel:
        return {
            "old_path": old_rel,
            "new_path": new_rel,
            "status": "invalid_paths",
        }

    if not old_rel.endswith(".py") or not new_rel.endswith(".py"):
        return {
            "old_path": old_rel,
            "new_path": new_rel,
            "status": "not_python_skip",
        }

    old_path = ROOT / old_rel
    new_path = ROOT / new_rel
    backup_path = BACKUP_ROOT / old_rel

    wrapper_content = make_wrapper_content(old_rel, new_rel)
    if wrapper_content is None:
        return {
            "old_path": old_rel,
            "new_path": new_rel,
            "status": "different_parent_skip",
        }

    # Idempotent durum: yeni dosya var ve eski dosya zaten wrapper ise başarılı say.
    if new_path.exists() and old_path.exists():
        existing = old_path.read_text(encoding="utf-8-sig", errors="ignore")
        if WRAPPER_MARKER in existing:
            return {
                "old_path": old_rel,
                "new_path": new_rel,
                "status": "already_wrapped",
            }

        return {
            "old_path": old_rel,
            "new_path": new_rel,
            "status": "target_exists_old_not_wrapper",
        }

    if not old_path.exists():
        return {
            "old_path": old_rel,
            "new_path": new_rel,
            "status": "old_source_missing",
        }

    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(old_path, backup_path)

    new_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(old_path), str(new_path))

    write_text(old_path, wrapper_content)

    return {
        "old_path": old_rel,
        "new_path": new_rel,
        "backup": str(backup_path),
        "status": "renamed_and_wrapper_created",
    }

def main():
    if not A10P_JSON.exists():
        raise SystemExit("A10P raporu bulunamadı. Önce A10P çalışmalı.")

    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    a10p = read_json(A10P_JSON)
    apply_candidates = [
        item for item in a10p.get("apply_candidates", [])
        if item.get("apply_allowed") is True
        and item.get("a10p_decision") == "python_compat_wrapper_candidate"
    ]

    operations = [apply_wrapper_rename(item) for item in apply_candidates]

    applied_count = sum(1 for x in operations if x.get("status") == "renamed_and_wrapper_created")
    already_wrapped_count = sum(1 for x in operations if x.get("status") == "already_wrapped")
    failed_count = sum(
        1 for x in operations
        if x.get("status") not in {"renamed_and_wrapper_created", "already_wrapped"}
    )

    old_modules = [module_name_from_path(x.get("old_path", "")) for x in operations]
    new_modules = [module_name_from_path(x.get("new_path", "")) for x in operations]
    modules = [m for m in old_modules + new_modules if m]

    import_code = (
        "import importlib\n"
        f"mods = {modules!r}\n"
        "for m in mods:\n"
        "    importlib.import_module(m)\n"
        "print('A10Q_IMPORT_SMOKE_OK')\n"
    )

    compile_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
        "migrations",
    ])

    import_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-c",
        import_code,
    ])

    pytest_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "pytest",
        "tests",
        "--ignore=tests/_archive_a5_obsolete",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
    ], timeout=1800)

    pytest_summary = parse_pytest_summary(pytest_result["combined"])

    ok = (
        a10p.get("ok") is True
        and len(apply_candidates) == 3
        and failed_count == 0
        and (applied_count + already_wrapped_count) == len(apply_candidates)
        and compile_result["returncode"] == 0
        and import_result["returncode"] == 0
        and pytest_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10Q_COMPAT_WRAPPER_RENAME_APPLY",
        "ok": ok,
        "decision": "A10Q_COMPAT_WRAPPER_RENAME_APPLY_GREEN" if ok else "A10Q_COMPAT_WRAPPER_RENAME_APPLY_NOT_GREEN",
        "a10p_ok": a10p.get("ok"),
        "backup_root": str(BACKUP_ROOT),
        "apply_candidate_count": len(apply_candidates),
        "applied_count": applied_count,
        "already_wrapped_count": already_wrapped_count,
        "failed_count": failed_count,
        "operations": operations,
        "old_modules": old_modules,
        "new_modules": new_modules,
        "compileall_returncode": compile_result["returncode"],
        "import_smoke_returncode": import_result["returncode"],
        "import_smoke_tail": import_result["combined"],
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "pytest_tail": pytest_result["combined"],
        "note": "A10Q yalnızca A10P apply_candidates listesindeki 3 Python dosyasını yeni ada taşıdı ve eski import yollarında compatibility wrapper bıraktı. Static, disabled ve Android debug dosyalarına dokunulmadı.",
        "next_action": "A10R: 45 referenced keep + 7 historical placeholder + 4 keep allowlist + 3 wrapper kararlarını final A10 evidence raporunda kapat.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10Q Compat Wrapper Rename Apply Kararı",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Karar: {result['decision']}",
        f"- A10P OK: {result['a10p_ok']}",
        f"- Backup root: `{result['backup_root']}`",
        f"- Apply candidate count: {result['apply_candidate_count']}",
        f"- Applied count: {result['applied_count']}",
        f"- Already wrapped count: {result['already_wrapped_count']}",
        f"- Failed count: {result['failed_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Import smoke returncode: {result['import_smoke_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        "",
        "## İşlemler",
        "",
        "```json",
        json.dumps(result["operations"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Eski Modül Yolları",
        "",
        "```json",
        json.dumps(result["old_modules"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Yeni Modül Yolları",
        "",
        "```json",
        json.dumps(result["new_modules"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Import Smoke",
        "",
        "```text",
        result["import_smoke_tail"],
        "```",
        "",
        "## Pytest Özeti",
        "",
        "```json",
        json.dumps(result["pytest_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Not",
        "",
        result["note"],
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A10Q_REPORT_JSON:", OUT_JSON)
    print("A10Q_REPORT_MD:", OUT_MD)
    print("A10Q_A10P_OK:", result["a10p_ok"])
    print("A10Q_BACKUP_ROOT:", result["backup_root"])
    print("A10Q_APPLY_CANDIDATE_COUNT:", result["apply_candidate_count"])
    print("A10Q_APPLIED_COUNT:", result["applied_count"])
    print("A10Q_ALREADY_WRAPPED_COUNT:", result["already_wrapped_count"])
    print("A10Q_FAILED_COUNT:", result["failed_count"])
    print("A10Q_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A10Q_IMPORT_SMOKE_RETURN_CODE:", result["import_smoke_returncode"])
    print("A10Q_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A10Q_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A10Q_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
