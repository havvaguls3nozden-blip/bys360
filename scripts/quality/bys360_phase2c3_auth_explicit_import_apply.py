from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import os
import re
import shutil
import subprocess

ROOT = Path(".").resolve()
ARCH = ROOT / "reports" / "architecture"
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

TARGET = Path("app/api/mobile/domains/auth.py")
BACKUP_ROOT = RELEASES / f"PHASE2C3_AUTH_EXPLICIT_IMPORT_BACKUP_{STAMP}"
RESTORE_PS1 = BACKUP_ROOT / "RESTORE_PHASE2C3_AUTH_EXPLICIT_IMPORT.ps1"

OUT_JSON = ARCH / "BYS360_PHASE2C3_AUTH_EXPLICIT_IMPORT_APPLY.json"
OUT_MD = ARCH / "BYS360_PHASE2C3_AUTH_EXPLICIT_IMPORT_APPLY.md"

NEW_IMPORT = (
    "from app.api.mobile.shared import "
    "User, _full_name, _issue_refresh_token, _issue_token, _load_refresh_token_user, "
    "mobile_api_bp, mobile_login_response, mobile_me_response, mobile_refresh_response, "
    "request, require_mobile_user"
)


def run_cmd(cmd, timeout=1800):
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
        "stdout": proc.stdout or "",
        "stderr": proc.stderr or "",
        "combined_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-50000:],
    }


def parse_pytest_summary(text: str) -> dict:
    summary = {}
    pattern = r"(\d+)\s+(failed|passed|error|errors|skipped|deselected|warning|warnings)\b"

    for num, key in re.findall(pattern, text or "", flags=re.IGNORECASE):
        key = key.lower()
        if key == "error":
            key = "errors"
        if key == "warning":
            key = "warnings"
        summary[key] = int(num)

    for key in ["failed", "passed", "errors", "skipped", "deselected", "warnings"]:
        summary.setdefault(key, 0)

    return summary


def write_restore_script(backup_file: Path) -> None:
    RESTORE_PS1.parent.mkdir(parents=True, exist_ok=True)
    RESTORE_PS1.write_text(
        "\n".join([
            '$ErrorActionPreference = "Stop"',
            'Set-Location "C:\\bys360\\project"',
            f'$src = "{backup_file}"',
            f'$dst = Join-Path "C:\\bys360\\project" "{TARGET.as_posix()}"',
            'if (Test-Path -LiteralPath $src) {',
            '  Copy-Item -LiteralPath $src -Destination $dst -Force',
            '}',
            'Write-Host "PHASE2C3 auth restore tamamlandı."',
        ]),
        encoding="utf-8",
    )


def run_full_gate(label: str) -> dict:
    py = ROOT / ".venv" / "Scripts" / "python.exe"

    compile_result = run_cmd([
        str(py), "-m", "compileall", "-q",
        "config.py", "app", "scripts", "tests", "migrations",
    ], timeout=900)

    contract = run_cmd([
        str(py), "-m", "pytest",
        "tests/architecture/test_phase2b_route_snapshot_contract.py",
        "-q", "-ra",
    ], timeout=900)

    auth_guard = run_cmd([
        str(py), "-m", "pytest",
        "tests/architecture/test_mobile_api_auth_guard_matrix_p4a.py",
        "-q", "-ra",
    ], timeout=900)

    default = run_cmd([
        str(py), "-m", "pytest",
        "-m", "not live and not realdb and not slow",
        "-q", "-ra",
    ], timeout=1800)

    contract_summary = parse_pytest_summary(contract["combined_tail"])
    auth_guard_summary = parse_pytest_summary(auth_guard["combined_tail"])
    default_summary = parse_pytest_summary(default["combined_tail"])

    ok = (
        compile_result["returncode"] == 0
        and contract["returncode"] == 0
        and auth_guard["returncode"] == 0
        and default["returncode"] == 0
        and contract_summary.get("failed", 0) == 0
        and contract_summary.get("errors", 0) == 0
        and auth_guard_summary.get("failed", 0) == 0
        and auth_guard_summary.get("errors", 0) == 0
        and default_summary.get("failed", 0) == 0
        and default_summary.get("errors", 0) == 0
        and default_summary.get("passed", 0) >= 700
    )

    return {
        "label": label,
        "ok": ok,
        "compileall_returncode": compile_result["returncode"],
        "contract_pytest_returncode": contract["returncode"],
        "contract_pytest_summary": contract_summary,
        "auth_guard_pytest_returncode": auth_guard["returncode"],
        "auth_guard_pytest_summary": auth_guard_summary,
        "auth_guard_tail": auth_guard["combined_tail"][-12000:],
        "default_pytest_returncode": default["returncode"],
        "default_pytest_summary": default_summary,
        "default_pytest_tail": default["combined_tail"][-12000:],
    }


def has_auth_shared_wildcard() -> bool:
    text = (ROOT / TARGET).read_text(encoding="utf-8-sig", errors="ignore")
    return bool(re.search(
        r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+\*\s*(?:#.*)?$",
        text,
        flags=re.MULTILINE,
    ))


def has_auth_explicit_import() -> bool:
    text = (ROOT / TARGET).read_text(encoding="utf-8-sig", errors="ignore")
    return NEW_IMPORT in text


def apply_change() -> dict:
    path = ROOT / TARGET
    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    lines = text.splitlines(keepends=True)

    changed = False
    old_line = None

    for idx, line in enumerate(lines):
        if re.match(
            r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+\*\s*(?:#.*)?$",
            line.strip(),
        ):
            indent = line[: len(line) - len(line.lstrip())]
            newline = "\n" if line.endswith("\n") else ""
            old_line = line.strip()
            lines[idx] = indent + NEW_IMPORT + newline
            changed = True
            break

    if changed:
        path.write_text("".join(lines), encoding="utf-8")

    return {
        "changed": changed,
        "old_line": old_line,
        "new_line": NEW_IMPORT if changed else None,
    }


def main() -> int:
    ARCH.mkdir(parents=True, exist_ok=True)
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    target_path = ROOT / TARGET
    backup_file = BACKUP_ROOT / TARGET
    backup_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target_path, backup_file)
    write_restore_script(backup_file)

    baseline = run_full_gate("baseline_before_auth_explicit_import")

    operation = {
        "changed": False,
        "old_line": None,
        "new_line": None,
    }

    if baseline["ok"]:
        operation = apply_change()
        after_gate = run_full_gate("after_auth_explicit_import")
    else:
        after_gate = {
            "ok": False,
            "reason": "baseline_not_green",
        }

    rollback_performed = False

    if not after_gate.get("ok"):
        shutil.copy2(backup_file, target_path)
        rollback_performed = True

    final_gate = run_full_gate("final_after_possible_restore")

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "PHASE2C3_AUTH_EXPLICIT_IMPORT_APPLY",
        "mode": "single_file_full_gate_with_auto_rollback",
        "ok": (
            baseline.get("ok") is True
            and operation.get("changed") is True
            and after_gate.get("ok") is True
            and rollback_performed is False
            and final_gate.get("ok") is True
            and has_auth_explicit_import()
            and not has_auth_shared_wildcard()
        ),
        "backup_root": str(BACKUP_ROOT),
        "restore_script": str(RESTORE_PS1),
        "target": TARGET.as_posix(),
        "operation": operation,
        "rollback_performed": rollback_performed,
        "baseline": baseline,
        "after_gate": after_gate,
        "final_gate": final_gate,
        "auth_has_shared_wildcard": has_auth_shared_wildcard(),
        "auth_has_explicit_import": has_auth_explicit_import(),
    }

    result["decision"] = (
        "PHASE2C3_GREEN_AUTH_EXPLICIT_IMPORT_APPLIED"
        if result["ok"]
        else "PHASE2C3_AUTH_RESTORED_OR_REVIEW_REQUIRED"
    )

    result["next_action"] = (
        "Faz 2C4 routes.py bilinçli facade import için ayrı değerlendirme yapılabilir."
        if result["ok"]
        else "auth.py özel helper import listesi daha ayrıntılı çıkarılmalı; dosya restore edildiyse güvenli haldedir."
    )

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 Faz 2C3 Auth Explicit Import Apply",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Target: `{result['target']}`",
        f"- Backup root: `{result['backup_root']}`",
        f"- Restore script: `{result['restore_script']}`",
        f"- Changed: {operation.get('changed')}",
        f"- Rollback performed: {result['rollback_performed']}",
        f"- Auth has shared wildcard: {result['auth_has_shared_wildcard']}",
        f"- Auth has explicit import: {result['auth_has_explicit_import']}",
        f"- Final default pytest returncode: {final_gate.get('default_pytest_returncode')}",
        f"- Final default pytest summary: `{json.dumps(final_gate.get('default_pytest_summary'), ensure_ascii=False)}`",
        "",
        "## Operation",
        "",
        "```json",
        json.dumps(operation, ensure_ascii=False, indent=2),
        "```",
        "",
        "## After Gate",
        "",
        "```json",
        json.dumps(after_gate, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Final Gate",
        "",
        "```json",
        json.dumps(final_gate, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("PHASE2C3_REPORT_JSON:", OUT_JSON)
    print("PHASE2C3_REPORT_MD:", OUT_MD)
    print("PHASE2C3_BACKUP_ROOT:", BACKUP_ROOT)
    print("PHASE2C3_RESTORE_SCRIPT:", RESTORE_PS1)
    print("PHASE2C3_CHANGED:", operation.get("changed"))
    print("PHASE2C3_ROLLBACK_PERFORMED:", rollback_performed)
    print("PHASE2C3_AUTH_HAS_SHARED_WILDCARD:", result["auth_has_shared_wildcard"])
    print("PHASE2C3_AUTH_HAS_EXPLICIT_IMPORT:", result["auth_has_explicit_import"])
    print("PHASE2C3_FINAL_DEFAULT_RETURN_CODE:", final_gate.get("default_pytest_returncode"))
    print("PHASE2C3_FINAL_DEFAULT_SUMMARY:", json.dumps(final_gate.get("default_pytest_summary"), ensure_ascii=False))
    print("PHASE2C3_OK:", result["ok"])

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
