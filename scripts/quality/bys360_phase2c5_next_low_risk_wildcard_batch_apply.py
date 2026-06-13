from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import os
import re
import shutil
import subprocess
from collections import Counter
import ast

ROOT = Path(".").resolve()
ARCH = ROOT / "reports" / "architecture"
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

PHASE2C1_SCRIPT = Path("scripts/quality/bys360_phase2c1_wildcard_import_explicit_plan.py")
PLAN_JSON = ARCH / "BYS360_PHASE2C1_WILDCARD_IMPORT_EXPLICIT_PLAN.json"

OUT_JSON = ARCH / "BYS360_PHASE2C5_NEXT_LOW_RISK_WILDCARD_BATCH_APPLY.json"
OUT_MD = ARCH / "BYS360_PHASE2C5_NEXT_LOW_RISK_WILDCARD_BATCH_APPLY.md"

BACKUP_ROOT = RELEASES / f"PHASE2C5_NEXT_LOW_RISK_WILDCARD_BATCH_BACKUP_{STAMP}"
RESTORE_PS1 = BACKUP_ROOT / "RESTORE_PHASE2C5_NEXT_LOW_RISK_WILDCARD_BATCH.ps1"

MAX_CANDIDATES = 5

SKIP_FILES = {
    "app/api/mobile/routes.py",  # C4 bilinçli facade istisnası.
}

SKIP_MODULES = {
    "app.api.mobile.shared",  # C4 bilinçli facade istisnası.
}


def run_cmd(cmd, timeout=1800):
    try:
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
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""

        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="ignore")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="ignore")

        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": 124,
            "stdout": stdout,
            "stderr": stderr,
            "combined_tail": (stdout + "\n" + stderr + "\nTIMEOUT")[-50000:],
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

    quality = run_cmd([
        str(py), "-m", "pytest",
        "tests/quality",
        "-m", "ci_safe",
        "-q", "-ra",
    ], timeout=900)

    default = run_cmd([
        str(py), "-m", "pytest",
        "-m", "not live and not realdb and not slow",
        "-q", "-ra",
    ], timeout=1800)

    contract_summary = parse_pytest_summary(contract["combined_tail"])
    auth_guard_summary = parse_pytest_summary(auth_guard["combined_tail"])
    quality_summary = parse_pytest_summary(quality["combined_tail"])
    default_summary = parse_pytest_summary(default["combined_tail"])

    ok = (
        compile_result["returncode"] == 0
        and contract["returncode"] == 0
        and auth_guard["returncode"] == 0
        and quality["returncode"] == 0
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
        "quality_smoke_returncode": quality["returncode"],
        "quality_smoke_summary": quality_summary,
        "default_pytest_returncode": default["returncode"],
        "default_pytest_summary": default_summary,
        "default_pytest_tail": default["combined_tail"][-12000:],
    }


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))


def iter_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_dicts(child)


def normalize_rel(path_value: str) -> str:
    return str(path_value or "").replace("\\", "/")


def current_line_matches(item: dict) -> bool:
    rel = normalize_rel(item.get("file"))
    line_no = int(item.get("line_no") or 0)
    module = item.get("module")

    path = ROOT / rel
    if not path.exists() or line_no < 1:
        return False

    lines = path.read_text(encoding="utf-8-sig", errors="ignore").splitlines()
    if line_no > len(lines):
        return False

    line = lines[line_no - 1].strip()
    expected_pattern = rf"^\s*from\s+{re.escape(str(module))}\s+import\s+\*\s*(?:#.*)?$"
    return bool(re.match(expected_pattern, line))


def collect_candidates(plan: dict) -> list[dict]:
    raw = []

    for item in iter_dicts(plan):
        rel = normalize_rel(item.get("file"))
        module = item.get("module")
        suggested = item.get("suggested_import_line")

        if not rel or not module or not suggested:
            continue

        if item.get("status") != "ready_for_explicit_import":
            continue

        if item.get("risk") != "low":
            continue

        if not rel.startswith("app/"):
            continue

        if rel in SKIP_FILES:
            continue

        if module in SKIP_MODULES:
            continue

        if not item.get("line_no"):
            continue

        if not current_line_matches(item):
            continue

        raw.append({
            "file": rel,
            "line_no": int(item["line_no"]),
            "module": module,
            "risk": item.get("risk"),
            "status": item.get("status"),
            "suggested_import_line": suggested,
        })

    deduped = []
    seen = set()

    for item in raw:
        key = (item["file"], item["line_no"], item["module"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    deduped.sort(key=lambda x: (x["module"], x["file"], x["line_no"]))
    return deduped[:MAX_CANDIDATES]


def backup_file(path: Path) -> Path:
    rel = path.relative_to(ROOT)
    dst = BACKUP_ROOT / "files" / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)
    return dst


def restore_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def write_restore_script(backups: list[dict]) -> None:
    lines = [
        '$ErrorActionPreference = "Stop"',
        'Set-Location "C:\\bys360\\project"',
        "",
    ]

    for item in backups:
        lines.extend([
            f'$src = "{item["backup_path"]}"',
            f'$dst = Join-Path "C:\\bys360\\project" "{item["relative_path"]}"',
            'if (Test-Path -LiteralPath $src) {',
            '  $parent = Split-Path -Parent $dst',
            '  if (!(Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }',
            '  Copy-Item -LiteralPath $src -Destination $dst -Force',
            '}',
            "",
        ])

    lines.append('Write-Host "PHASE2C5 restore tamamlandı."')
    RESTORE_PS1.parent.mkdir(parents=True, exist_ok=True)
    RESTORE_PS1.write_text("\n".join(lines), encoding="utf-8")


def replace_import_line(item: dict) -> dict:
    rel = item["file"]
    path = ROOT / rel
    line_no = int(item["line_no"])
    module = item["module"]
    suggested = item["suggested_import_line"]

    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    lines = text.splitlines(keepends=True)

    if line_no < 1 or line_no > len(lines):
        return {
            "file": rel,
            "changed": False,
            "reason": "line_no_out_of_range",
        }

    old_line = lines[line_no - 1]
    stripped = old_line.strip()
    expected_pattern = rf"^\s*from\s+{re.escape(module)}\s+import\s+\*\s*(?:#.*)?$"

    if not re.match(expected_pattern, stripped):
        return {
            "file": rel,
            "changed": False,
            "reason": "line_content_not_expected",
            "actual": stripped,
            "expected_pattern": expected_pattern,
        }

    newline = "\n" if old_line.endswith("\n") else ""
    indent = old_line[: len(old_line) - len(old_line.lstrip())]

    lines[line_no - 1] = indent + suggested + newline
    path.write_text("".join(lines), encoding="utf-8")

    return {
        "file": rel,
        "module": module,
        "changed": True,
        "old_line": stripped,
        "new_line": suggested,
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


def main() -> int:
    ARCH.mkdir(parents=True, exist_ok=True)
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    py = ROOT / ".venv" / "Scripts" / "python.exe"

    phase2c1_before = run_cmd([str(py), str(PHASE2C1_SCRIPT)], timeout=1800)
    plan = read_json(PLAN_JSON)
    candidates = collect_candidates(plan)

    before_wildcards = app_wildcards()
    before_by_module = Counter(str(row.get("module")) for row in before_wildcards)

    baseline = run_full_gate("baseline_before_phase2c5")

    backups = []
    operations = []

    if baseline["ok"]:
        for item in candidates:
            rel = item["file"]
            path = ROOT / rel

            backup_path = backup_file(path)
            backups.append({
                "relative_path": rel,
                "backup_path": str(backup_path),
            })

            operation = replace_import_line(item)

            if not operation.get("changed"):
                restore_file(backup_path, path)
                operation["kept"] = False
                operation["gate"] = None
                operations.append(operation)
                continue

            gate = run_full_gate(f"full_gate_after_{rel}")

            if gate["ok"]:
                operation["kept"] = True
                operation["gate"] = {
                    "ok": True,
                    "default_pytest_returncode": gate["default_pytest_returncode"],
                    "default_pytest_summary": gate["default_pytest_summary"],
                }
            else:
                restore_file(backup_path, path)
                operation["kept"] = False
                operation["gate"] = {
                    "ok": False,
                    "default_pytest_returncode": gate["default_pytest_returncode"],
                    "default_pytest_summary": gate["default_pytest_summary"],
                    "default_pytest_tail": gate["default_pytest_tail"],
                }

            operations.append(operation)

    write_restore_script(backups)

    final_gate = run_full_gate("final_after_phase2c5")

    rollback_all_performed = False
    if not final_gate["ok"]:
        for item in reversed(backups):
            restore_file(Path(item["backup_path"]), ROOT / item["relative_path"])

        rollback_all_performed = True
        final_gate = run_full_gate("final_after_phase2c5_restore_all")

    phase2c1_after = run_cmd([str(py), str(PHASE2C1_SCRIPT)], timeout=1800)

    after_wildcards = app_wildcards()
    after_by_module = Counter(str(row.get("module")) for row in after_wildcards)

    kept_count = sum(1 for item in operations if item.get("kept"))
    rolled_back_count = sum(1 for item in operations if not item.get("kept"))

    ok = (
        baseline.get("ok") is True
        and final_gate.get("ok") is True
        and rollback_all_performed is False
        and kept_count >= 1
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "PHASE2C5_NEXT_LOW_RISK_WILDCARD_BATCH_APPLY",
        "mode": "one_by_one_low_risk_non_mobile_shared_full_gate",
        "ok": ok,
        "decision": "PHASE2C5_GREEN_LOW_RISK_BATCH_APPLIED" if ok else "PHASE2C5_NO_SAFE_KEEP_OR_REVIEW_REQUIRED",
        "max_candidates": MAX_CANDIDATES,
        "candidate_count": len(candidates),
        "kept_count": kept_count,
        "rolled_back_count": rolled_back_count,
        "rollback_all_performed": rollback_all_performed,
        "backup_root": str(BACKUP_ROOT),
        "restore_script": str(RESTORE_PS1),
        "skipped_files": sorted(SKIP_FILES),
        "skipped_modules": sorted(SKIP_MODULES),
        "candidates": candidates,
        "operations": operations,
        "before_app_ast_wildcard_count": len(before_wildcards),
        "after_app_ast_wildcard_count": len(after_wildcards),
        "before_app_ast_wildcard_by_module_top_50": dict(before_by_module.most_common(50)),
        "after_app_ast_wildcard_by_module_top_50": dict(after_by_module.most_common(50)),
        "phase2c1_before_returncode": phase2c1_before["returncode"],
        "phase2c1_after_returncode": phase2c1_after["returncode"],
        "baseline": baseline,
        "final_gate": final_gate,
        "next_action": "Faz 2C6 kalan wildcard sınıflandırma raporuna geçilebilir." if ok else "C5 raporundaki adaylar incelenmeli; gerekiyorsa daha küçük/manuel paket yapılmalı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 Faz 2C5 Next Low Risk Wildcard Batch Apply",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Candidate count: {result['candidate_count']}",
        f"- Kept count: {result['kept_count']}",
        f"- Rolled back count: {result['rolled_back_count']}",
        f"- Rollback all performed: {result['rollback_all_performed']}",
        f"- Before app AST wildcard count: {result['before_app_ast_wildcard_count']}",
        f"- After app AST wildcard count: {result['after_app_ast_wildcard_count']}",
        f"- Final default pytest returncode: {final_gate.get('default_pytest_returncode')}",
        f"- Final default pytest summary: `{json.dumps(final_gate.get('default_pytest_summary'), ensure_ascii=False)}`",
        f"- Backup root: `{result['backup_root']}`",
        f"- Restore script: `{result['restore_script']}`",
        "",
        "## Candidates",
        "",
        "```json",
        json.dumps(candidates, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Operations",
        "",
        "```json",
        json.dumps(operations, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Before Wildcard By Module Top 50",
        "",
        "```json",
        json.dumps(result["before_app_ast_wildcard_by_module_top_50"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## After Wildcard By Module Top 50",
        "",
        "```json",
        json.dumps(result["after_app_ast_wildcard_by_module_top_50"], ensure_ascii=False, indent=2),
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

    print("PHASE2C5_REPORT_JSON:", OUT_JSON)
    print("PHASE2C5_REPORT_MD:", OUT_MD)
    print("PHASE2C5_BACKUP_ROOT:", BACKUP_ROOT)
    print("PHASE2C5_RESTORE_SCRIPT:", RESTORE_PS1)
    print("PHASE2C5_CANDIDATE_COUNT:", result["candidate_count"])
    print("PHASE2C5_KEPT_COUNT:", result["kept_count"])
    print("PHASE2C5_ROLLED_BACK_COUNT:", result["rolled_back_count"])
    print("PHASE2C5_ROLLBACK_ALL_PERFORMED:", result["rollback_all_performed"])
    print("PHASE2C5_BEFORE_APP_AST_WILDCARD_COUNT:", result["before_app_ast_wildcard_count"])
    print("PHASE2C5_AFTER_APP_AST_WILDCARD_COUNT:", result["after_app_ast_wildcard_count"])
    print("PHASE2C5_FINAL_DEFAULT_RETURN_CODE:", final_gate.get("default_pytest_returncode"))
    print("PHASE2C5_FINAL_DEFAULT_SUMMARY:", json.dumps(final_gate.get("default_pytest_summary"), ensure_ascii=False))
    print("PHASE2C5_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
