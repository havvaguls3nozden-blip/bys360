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

PLAN_JSON = ARCH / "BYS360_PHASE2C1_WILDCARD_IMPORT_EXPLICIT_PLAN.json"
OUT_JSON = ARCH / "BYS360_PHASE2C2_SAFE_SUBSET_MOBILE_SHARED_WILDCARD_APPLY.json"
OUT_MD = ARCH / "BYS360_PHASE2C2_SAFE_SUBSET_MOBILE_SHARED_WILDCARD_APPLY.md"

BACKUP_ROOT = RELEASES / f"PHASE2C2_SAFE_SUBSET_BACKUP_{STAMP}"
RESTORE_PS1 = BACKUP_ROOT / "RESTORE_PHASE2C2_SAFE_SUBSET.ps1"

SKIP_FILES = {
    "app/api/mobile/routes.py",  # Bilinçli facade import; ayrı ele alınacak.
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
            "combined_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-40000:],
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
            "combined_tail": (stdout + "\n" + stderr + "\nTIMEOUT")[-40000:],
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


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))


def get_candidates(plan: dict) -> list[dict]:
    items = []
    for item in plan.get("first_apply_candidates") or []:
        file_name = item.get("file", "")
        if file_name in SKIP_FILES:
            continue
        if (
            item.get("status") == "ready_for_explicit_import"
            and item.get("risk") == "low"
            and file_name.startswith("app/api/mobile/")
            and item.get("module") == "app.api.mobile.shared"
            and item.get("suggested_import_line")
        ):
            items.append(item)
    return items


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

    lines.append('Write-Host "PHASE2C2 safe subset restore tamamlandı."')
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
        "changed": True,
        "old_line": stripped,
        "new_line": suggested,
    }


def count_all_wildcards() -> int:
    count = 0
    pattern = r"^\s*from\s+[\w\.]+\s+import\s+\*\s*(?:#.*)?$"

    for path in ROOT.rglob("*.py"):
        rel_parts = {part.lower() for part in path.relative_to(ROOT).parts}
        if rel_parts & {".git", ".venv", "venv", "reports", "releases", "__pycache__", "node_modules"}:
            continue

        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        count += len(re.findall(pattern, text, flags=re.MULTILINE))

    return count


def validation(label: str, full: bool = False) -> dict:
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

    quality = run_cmd([
        str(py), "-m", "pytest",
        "tests/quality",
        "-m", "ci_safe",
        "-q", "-ra",
    ], timeout=900)

    result = {
        "label": label,
        "compileall_returncode": compile_result["returncode"],
        "contract_pytest_returncode": contract["returncode"],
        "contract_pytest_summary": parse_pytest_summary(contract["combined_tail"]),
        "quality_smoke_returncode": quality["returncode"],
        "quality_smoke_summary": parse_pytest_summary(quality["combined_tail"]),
    }

    if full:
        default = run_cmd([
            str(py), "-m", "pytest",
            "-m", "not live and not realdb and not slow",
            "-q", "-ra",
        ], timeout=1800)

        result.update({
            "default_pytest_returncode": default["returncode"],
            "default_pytest_summary": parse_pytest_summary(default["combined_tail"]),
            "default_pytest_tail": default["combined_tail"][-12000:],
        })

    return result


def validation_green(v: dict, full: bool = False) -> bool:
    ok = (
        v["compileall_returncode"] == 0
        and v["contract_pytest_returncode"] == 0
        and v["quality_smoke_returncode"] == 0
        and v["contract_pytest_summary"].get("failed", 0) == 0
        and v["contract_pytest_summary"].get("errors", 0) == 0
    )

    if full:
        default_summary = v.get("default_pytest_summary", {})
        ok = (
            ok
            and v.get("default_pytest_returncode") == 0
            and default_summary.get("failed", 0) == 0
            and default_summary.get("errors", 0) == 0
            and default_summary.get("passed", 0) >= 700
        )

    return ok


def main() -> int:
    ARCH.mkdir(parents=True, exist_ok=True)
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    plan = read_json(PLAN_JSON)
    candidates = get_candidates(plan)

    before_wildcards = count_all_wildcards()

    backups = []
    operations = []

    for item in candidates:
        rel = item["file"]
        path = ROOT / rel

        backup_path = backup_file(path)
        backup_info = {
            "relative_path": rel,
            "backup_path": str(backup_path),
        }
        backups.append(backup_info)

        op = replace_import_line(item)

        if not op.get("changed"):
            restore_file(backup_path, path)
            op["kept"] = False
            op["validation"] = None
            operations.append(op)
            continue

        small_validation = validation(f"after_{rel}", full=False)

        if validation_green(small_validation, full=False):
            op["kept"] = True
            op["validation"] = small_validation
        else:
            restore_file(backup_path, path)
            op["kept"] = False
            op["validation"] = small_validation

        operations.append(op)

    write_restore_script(backups)

    after_subset_wildcards = count_all_wildcards()
    final_validation = validation("final_full_validation", full=True)

    final_ok = validation_green(final_validation, full=True)

    if not final_ok:
        for item in reversed(backups):
            restore_file(Path(item["backup_path"]), ROOT / item["relative_path"])

    final_wildcards = count_all_wildcards()
    final_validation_after_possible_restore = validation("after_possible_restore", full=True)

    kept_count = sum(1 for op in operations if op.get("kept"))
    rolled_back_count = sum(1 for op in operations if not op.get("kept"))

    ok = (
        final_ok
        and final_wildcards == before_wildcards - kept_count
        and final_validation_after_possible_restore.get("default_pytest_returncode") == 0
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "PHASE2C2_SAFE_SUBSET_MOBILE_SHARED_WILDCARD_APPLY",
        "mode": "one_by_one_safe_subset_apply",
        "ok": ok,
        "decision": "PHASE2C2_SAFE_SUBSET_GREEN" if ok else "PHASE2C2_SAFE_SUBSET_REVIEW_OR_RESTORED",
        "backup_root": str(BACKUP_ROOT),
        "restore_script": str(RESTORE_PS1),
        "skipped_files": sorted(SKIP_FILES),
        "candidate_count": len(candidates),
        "kept_count": kept_count,
        "rolled_back_count": rolled_back_count,
        "before_wildcards": before_wildcards,
        "after_subset_wildcards": after_subset_wildcards,
        "final_wildcards": final_wildcards,
        "operations": operations,
        "final_validation": final_validation,
        "final_validation_after_possible_restore": final_validation_after_possible_restore,
        "next_action": "Faz 2C3 güvenli kalan ikinci paket planlanabilir." if ok else "Final validation bozulduğu için güvenli duruma restore edildi; failure tail incelenmeli.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 Faz 2C2 Safe Subset Mobile Shared Wildcard Apply",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Backup root: `{result['backup_root']}`",
        f"- Restore script: `{result['restore_script']}`",
        f"- Skipped files: `{', '.join(result['skipped_files'])}`",
        f"- Candidate count: {result['candidate_count']}",
        f"- Kept count: {result['kept_count']}",
        f"- Rolled back count: {result['rolled_back_count']}",
        f"- Before wildcards: {result['before_wildcards']}",
        f"- Final wildcards: {result['final_wildcards']}",
        "",
        "## Operations",
        "",
        "```json",
        json.dumps(operations, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Final Validation",
        "",
        "```json",
        json.dumps(final_validation, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Final Validation After Possible Restore",
        "",
        "```json",
        json.dumps(final_validation_after_possible_restore, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("PHASE2C2_SAFE_REPORT_JSON:", OUT_JSON)
    print("PHASE2C2_SAFE_REPORT_MD:", OUT_MD)
    print("PHASE2C2_SAFE_BACKUP_ROOT:", BACKUP_ROOT)
    print("PHASE2C2_SAFE_RESTORE_SCRIPT:", RESTORE_PS1)
    print("PHASE2C2_SAFE_CANDIDATE_COUNT:", result["candidate_count"])
    print("PHASE2C2_SAFE_KEPT_COUNT:", result["kept_count"])
    print("PHASE2C2_SAFE_ROLLED_BACK_COUNT:", result["rolled_back_count"])
    print("PHASE2C2_SAFE_BEFORE_WILDCARDS:", result["before_wildcards"])
    print("PHASE2C2_SAFE_FINAL_WILDCARDS:", result["final_wildcards"])
    print("PHASE2C2_SAFE_FINAL_DEFAULT_RETURN_CODE:", final_validation_after_possible_restore.get("default_pytest_returncode"))
    print("PHASE2C2_SAFE_FINAL_DEFAULT_SUMMARY:", json.dumps(final_validation_after_possible_restore.get("default_pytest_summary"), ensure_ascii=False))
    print("PHASE2C2_SAFE_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
