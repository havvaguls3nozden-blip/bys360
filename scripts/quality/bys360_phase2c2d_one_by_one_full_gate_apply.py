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
OUT_JSON = ARCH / "BYS360_PHASE2C2D_ONE_BY_ONE_FULL_GATE_APPLY.json"
OUT_MD = ARCH / "BYS360_PHASE2C2D_ONE_BY_ONE_FULL_GATE_APPLY.md"

BACKUP_ROOT = RELEASES / f"PHASE2C2D_ONE_BY_ONE_FULL_GATE_BACKUP_{STAMP}"
RESTORE_PS1 = BACKUP_ROOT / "RESTORE_PHASE2C2D_ONE_BY_ONE_FULL_GATE.ps1"

SKIP_FILES = {
    "app/api/mobile/routes.py",  # Bilinçli facade import; ayrı fazda ele alınacak.
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


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))


def get_candidates(plan: dict) -> list[dict]:
    rows = []
    for item in plan.get("first_apply_candidates") or []:
        rel = item.get("file", "")
        if rel in SKIP_FILES:
            continue

        if (
            item.get("status") == "ready_for_explicit_import"
            and item.get("risk") == "low"
            and rel.startswith("app/api/mobile/")
            and item.get("module") == "app.api.mobile.shared"
            and item.get("suggested_import_line")
        ):
            rows.append(item)

    return rows


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

    lines.append('Write-Host "PHASE2C2D restore tamamlandı."')
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


def file_has_mobile_shared_wildcard(rel: str) -> bool:
    text = (ROOT / rel).read_text(encoding="utf-8-sig", errors="ignore")
    return bool(re.search(
        r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+\*\s*(?:#.*)?$",
        text,
        flags=re.MULTILINE,
    ))


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
    quality_summary = parse_pytest_summary(quality["combined_tail"])
    default_summary = parse_pytest_summary(default["combined_tail"])

    ok = (
        compile_result["returncode"] == 0
        and contract["returncode"] == 0
        and quality["returncode"] == 0
        and default["returncode"] == 0
        and contract_summary.get("failed", 0) == 0
        and contract_summary.get("errors", 0) == 0
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
        "quality_smoke_returncode": quality["returncode"],
        "quality_smoke_summary": quality_summary,
        "default_pytest_returncode": default["returncode"],
        "default_pytest_summary": default_summary,
        "default_pytest_tail": default["combined_tail"][-12000:],
    }


def target_status(candidates: list[dict]) -> list[dict]:
    rows = []

    for item in candidates:
        rel = item["file"]
        rows.append({
            "file": rel,
            "has_mobile_shared_wildcard": file_has_mobile_shared_wildcard(rel),
            "has_explicit_mobile_shared_import": bool(re.search(
                r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+(?!\*)",
                (ROOT / rel).read_text(encoding="utf-8-sig", errors="ignore"),
                flags=re.MULTILINE,
            )),
        })

    return rows


def main() -> int:
    ARCH.mkdir(parents=True, exist_ok=True)
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    plan = read_json(PLAN_JSON)
    candidates = get_candidates(plan)

    backups = []
    operations = []

    baseline = run_full_gate("baseline_before_phase2c2d")

    if not baseline["ok"]:
        result = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "phase": "PHASE2C2D_ONE_BY_ONE_FULL_GATE_APPLY",
            "ok": False,
            "decision": "BASELINE_NOT_GREEN_STOPPED",
            "candidate_count": len(candidates),
            "baseline": baseline,
            "operations": [],
            "next_action": "Önce baseline test yeşile alınmalı.",
        }
        OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        OUT_MD.write_text("# BYS360 Faz 2C2D\n\nBaseline yeşil değil; işlem yapılmadı.\n", encoding="utf-8")
        print("PHASE2C2D_OK:", False)
        print("PHASE2C2D_DECISION:", result["decision"])
        return 1

    for item in candidates:
        rel = item["file"]
        path = ROOT / rel
        backup_path = backup_file(path)
        backups.append({
            "relative_path": rel,
            "backup_path": str(backup_path),
        })

        op = replace_import_line(item)

        if not op.get("changed"):
            restore_file(backup_path, path)
            op["kept"] = False
            op["gate"] = None
            operations.append(op)
            continue

        gate = run_full_gate(f"full_gate_after_{rel}")

        if gate["ok"]:
            op["kept"] = True
            op["gate"] = {
                "ok": gate["ok"],
                "default_pytest_summary": gate["default_pytest_summary"],
                "default_pytest_returncode": gate["default_pytest_returncode"],
            }
        else:
            restore_file(backup_path, path)
            op["kept"] = False
            op["gate"] = {
                "ok": gate["ok"],
                "default_pytest_summary": gate["default_pytest_summary"],
                "default_pytest_returncode": gate["default_pytest_returncode"],
                "default_pytest_tail": gate["default_pytest_tail"],
            }

        operations.append(op)

    write_restore_script(backups)

    final_gate = run_full_gate("final_after_phase2c2d")
    final_status = target_status(candidates)

    if not final_gate["ok"]:
        for item in reversed(backups):
            restore_file(Path(item["backup_path"]), ROOT / item["relative_path"])

        final_gate_after_restore = run_full_gate("final_after_restore")
    else:
        final_gate_after_restore = final_gate

    kept_count = sum(1 for item in operations if item.get("kept"))
    rolled_back_count = sum(1 for item in operations if not item.get("kept"))

    ok = (
        final_gate_after_restore["ok"]
        and kept_count >= 1
        and all(not row["has_mobile_shared_wildcard"] for row in target_status([op for op in candidates if any(o.get("file") == op.get("file") and o.get("kept") for o in operations)]))
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "PHASE2C2D_ONE_BY_ONE_FULL_GATE_APPLY",
        "mode": "apply_each_candidate_only_if_full_default_pytest_passes",
        "ok": ok,
        "decision": "PHASE2C2D_GREEN_PARTIAL_SAFE_APPLY" if ok else "PHASE2C2D_REVIEW_REQUIRED",
        "backup_root": str(BACKUP_ROOT),
        "restore_script": str(RESTORE_PS1),
        "skipped_files": sorted(SKIP_FILES),
        "candidate_count": len(candidates),
        "kept_count": kept_count,
        "rolled_back_count": rolled_back_count,
        "operations": operations,
        "final_target_status": final_status,
        "final_gate": final_gate,
        "final_gate_after_possible_restore": final_gate_after_restore,
        "next_action": "Faz 2C3 için kalan güvenli paket planlanabilir." if ok else "Hangi dosyanın full gate bozduğu rapordan incelenmeli.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 Faz 2C2D One-by-One Full Gate Apply",
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
        f"- Final default pytest returncode: {final_gate_after_restore['default_pytest_returncode']}",
        "",
        "## Operations",
        "",
        "```json",
        json.dumps(operations, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Final Target Status",
        "",
        "```json",
        json.dumps(final_status, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Final Gate After Possible Restore",
        "",
        "```json",
        json.dumps(final_gate_after_restore, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("PHASE2C2D_REPORT_JSON:", OUT_JSON)
    print("PHASE2C2D_REPORT_MD:", OUT_MD)
    print("PHASE2C2D_BACKUP_ROOT:", BACKUP_ROOT)
    print("PHASE2C2D_RESTORE_SCRIPT:", RESTORE_PS1)
    print("PHASE2C2D_CANDIDATE_COUNT:", result["candidate_count"])
    print("PHASE2C2D_KEPT_COUNT:", result["kept_count"])
    print("PHASE2C2D_ROLLED_BACK_COUNT:", result["rolled_back_count"])
    print("PHASE2C2D_FINAL_DEFAULT_RETURN_CODE:", final_gate_after_restore["default_pytest_returncode"])
    print("PHASE2C2D_FINAL_DEFAULT_SUMMARY:", json.dumps(final_gate_after_restore["default_pytest_summary"], ensure_ascii=False))
    print("PHASE2C2D_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
