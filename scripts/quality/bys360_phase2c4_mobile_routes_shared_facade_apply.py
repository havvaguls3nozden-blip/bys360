from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter
import ast
import json
import os
import re
import shutil
import subprocess

ROOT = Path(".").resolve()
ARCH = ROOT / "reports" / "architecture"
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

TARGET = Path("app/api/mobile/routes.py")
SHARED = Path("app/api/mobile/shared.py")

BACKUP_ROOT = RELEASES / f"PHASE2C4_MOBILE_ROUTES_SHARED_FACADE_BACKUP_{STAMP}"
RESTORE_PS1 = BACKUP_ROOT / "RESTORE_PHASE2C4_MOBILE_ROUTES_SHARED_FACADE.ps1"

OUT_JSON = ARCH / "BYS360_PHASE2C4_MOBILE_ROUTES_SHARED_FACADE_APPLY.json"
OUT_MD = ARCH / "BYS360_PHASE2C4_MOBILE_ROUTES_SHARED_FACADE_APPLY.md"


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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def collect_defined_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    names.add(alias.asname or alias.name)

        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            else:
                targets = [node.target]

            for target in targets:
                for child in ast.walk(target):
                    if isinstance(child, ast.Name):
                        names.add(child.id)

    return names


def collect_loaded_names(tree: ast.AST) -> set[str]:
    return {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }


def shared_symbols() -> set[str]:
    tree = ast.parse(read_text(ROOT / SHARED), filename=str(ROOT / SHARED))
    return collect_defined_names(tree)


def current_shared_wildcard_exists() -> bool:
    text = read_text(ROOT / TARGET)
    return bool(re.search(
        r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+\*\s*(?:#.*)?$",
        text,
        flags=re.MULTILINE,
    ))


def current_shared_explicit_exists() -> bool:
    text = read_text(ROOT / TARGET)
    return bool(re.search(
        r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+(?!\*)",
        text,
        flags=re.MULTILINE,
    ))


def build_candidate_import() -> dict:
    target_tree = ast.parse(read_text(ROOT / TARGET), filename=str(ROOT / TARGET))
    shared = shared_symbols()

    loaded = collect_loaded_names(target_tree)
    defined = collect_defined_names(target_tree)

    candidate_names = sorted((loaded - defined) & shared)

    # routes.py facade dosyasında decorator ve test sözleşmesi için bu isimler özellikle korunur.
    for name in ["mobile_api_bp", "User", "jsonify", "request"]:
        if name in shared and name not in candidate_names:
            candidate_names.append(name)

    candidate_names = sorted(set(candidate_names))

    return {
        "candidate_names": candidate_names,
        "candidate_count": len(candidate_names),
        "candidate_import_line": (
            "from app.api.mobile.shared import " + ", ".join(candidate_names)
            if candidate_names
            else None
        ),
    }


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
            'Write-Host "PHASE2C4 routes.py restore tamamlandı."',
        ]),
        encoding="utf-8",
    )


def apply_change(candidate_import_line: str | None) -> dict:
    if not candidate_import_line:
        return {
            "changed": False,
            "reason": "empty_candidate_import_line",
        }

    path = ROOT / TARGET
    text = read_text(path)
    lines = text.splitlines(keepends=True)

    for idx, line in enumerate(lines):
        if re.match(
            r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+\*\s*(?:#.*)?$",
            line.strip(),
        ):
            indent = line[: len(line) - len(line.lstrip())]
            newline = "\n" if line.endswith("\n") else ""
            old_line = line.strip()
            lines[idx] = indent + candidate_import_line + newline
            path.write_text("".join(lines), encoding="utf-8")
            return {
                "changed": True,
                "old_line": old_line,
                "new_line": candidate_import_line,
            }

    return {
        "changed": False,
        "reason": "shared_wildcard_line_not_found",
    }


def app_wildcards() -> list[dict]:
    rows = []

    for path in sorted((ROOT / "app").rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig", errors="ignore"), filename=str(path))
        except Exception as exc:
            rows.append({
                "file": rel,
                "line_no": None,
                "module": None,
                "error": str(exc),
            })
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
                rows.append({
                    "file": rel,
                    "line_no": node.lineno,
                    "module": node.module,
                    "level": node.level,
                })

    return rows


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
        "default_pytest_returncode": default["returncode"],
        "default_pytest_summary": default_summary,
        "default_pytest_tail": default["combined_tail"][-12000:],
    }


def main() -> int:
    ARCH.mkdir(parents=True, exist_ok=True)
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    target_path = ROOT / TARGET
    backup_file = BACKUP_ROOT / TARGET
    backup_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target_path, backup_file)
    write_restore_script(backup_file)

    before_wildcards = app_wildcards()
    before_mobile_shared_remaining = [
        row for row in before_wildcards
        if row.get("module") == "app.api.mobile.shared"
    ]

    candidate = build_candidate_import()
    baseline = run_full_gate("baseline_before_routes_facade_apply")

    if baseline["ok"] and current_shared_wildcard_exists():
        operation = apply_change(candidate["candidate_import_line"])
        after_gate = run_full_gate("after_routes_facade_apply")
    else:
        operation = {
            "changed": False,
            "reason": "baseline_not_green_or_no_shared_wildcard",
        }
        after_gate = {
            "ok": False,
            "reason": "not_attempted",
        }

    rollback_performed = False

    if not after_gate.get("ok"):
        shutil.copy2(backup_file, target_path)
        rollback_performed = operation.get("changed") is True

    final_gate = run_full_gate("final_after_possible_restore")

    after_wildcards = app_wildcards()
    after_mobile_shared_remaining = [
        row for row in after_wildcards
        if row.get("module") == "app.api.mobile.shared"
    ]

    ok = (
        baseline.get("ok") is True
        and operation.get("changed") is True
        and after_gate.get("ok") is True
        and rollback_performed is False
        and final_gate.get("ok") is True
        and not current_shared_wildcard_exists()
        and current_shared_explicit_exists()
        and len(after_mobile_shared_remaining) == 0
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "PHASE2C4_MOBILE_ROUTES_SHARED_FACADE_APPLY",
        "mode": "single_facade_shared_wildcard_to_explicit_import_with_full_gate",
        "ok": ok,
        "decision": "PHASE2C4_GREEN_ROUTES_SHARED_FACADE_EXPLICIT" if ok else "PHASE2C4_ROUTES_FACADE_RESTORED_OR_REVIEW_REQUIRED",
        "target": TARGET.as_posix(),
        "backup_root": str(BACKUP_ROOT),
        "restore_script": str(RESTORE_PS1),
        "candidate": candidate,
        "operation": operation,
        "rollback_performed": rollback_performed,
        "before_app_ast_wildcard_count": len(before_wildcards),
        "after_app_ast_wildcard_count": len(after_wildcards),
        "before_mobile_shared_remaining": before_mobile_shared_remaining,
        "after_mobile_shared_remaining": after_mobile_shared_remaining,
        "routes_has_shared_wildcard": current_shared_wildcard_exists(),
        "routes_has_shared_explicit": current_shared_explicit_exists(),
        "baseline": baseline,
        "after_gate": after_gate,
        "final_gate": final_gate,
        "next_action": "Faz 2C5 ikinci wildcard import paketi seçilebilir." if ok else "routes.py facade wildcard bilinçli istisna olarak bırakılmalı veya eksik isimler rapordan elle eklenmeli.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 Faz 2C4 Mobile Routes Shared Facade Apply",
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
        f"- Candidate count: {candidate['candidate_count']}",
        f"- Changed: {operation.get('changed')}",
        f"- Rollback performed: {rollback_performed}",
        f"- Before app AST wildcard count: {result['before_app_ast_wildcard_count']}",
        f"- After app AST wildcard count: {result['after_app_ast_wildcard_count']}",
        f"- Before mobile shared remaining: {len(before_mobile_shared_remaining)}",
        f"- After mobile shared remaining: {len(after_mobile_shared_remaining)}",
        f"- Routes has shared wildcard: {result['routes_has_shared_wildcard']}",
        f"- Routes has shared explicit: {result['routes_has_shared_explicit']}",
        f"- Final default pytest returncode: {final_gate.get('default_pytest_returncode')}",
        f"- Final default pytest summary: `{json.dumps(final_gate.get('default_pytest_summary'), ensure_ascii=False)}`",
        "",
        "## Candidate",
        "",
        "```json",
        json.dumps(candidate, ensure_ascii=False, indent=2),
        "```",
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

    print("PHASE2C4_REPORT_JSON:", OUT_JSON)
    print("PHASE2C4_REPORT_MD:", OUT_MD)
    print("PHASE2C4_BACKUP_ROOT:", BACKUP_ROOT)
    print("PHASE2C4_RESTORE_SCRIPT:", RESTORE_PS1)
    print("PHASE2C4_CANDIDATE_COUNT:", candidate["candidate_count"])
    print("PHASE2C4_CHANGED:", operation.get("changed"))
    print("PHASE2C4_ROLLBACK_PERFORMED:", rollback_performed)
    print("PHASE2C4_BEFORE_APP_AST_WILDCARD_COUNT:", len(before_wildcards))
    print("PHASE2C4_AFTER_APP_AST_WILDCARD_COUNT:", len(after_wildcards))
    print("PHASE2C4_BEFORE_MOBILE_SHARED_REMAINING_COUNT:", len(before_mobile_shared_remaining))
    print("PHASE2C4_AFTER_MOBILE_SHARED_REMAINING_COUNT:", len(after_mobile_shared_remaining))
    print("PHASE2C4_ROUTES_HAS_SHARED_WILDCARD:", result["routes_has_shared_wildcard"])
    print("PHASE2C4_ROUTES_HAS_SHARED_EXPLICIT:", result["routes_has_shared_explicit"])
    print("PHASE2C4_FINAL_DEFAULT_RETURN_CODE:", final_gate.get("default_pytest_returncode"))
    print("PHASE2C4_FINAL_DEFAULT_SUMMARY:", json.dumps(final_gate.get("default_pytest_summary"), ensure_ascii=False))
    print("PHASE2C4_OK:", result["ok"])

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
