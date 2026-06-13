from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter
import ast
import json
import os
import re
import subprocess

ROOT = Path(".").resolve()
ARCH = ROOT / "reports" / "architecture"

OUT_JSON = ARCH / "BYS360_PHASE2C2Z_SAFE_SUBSET_FINAL_VERIFY.json"
OUT_MD = ARCH / "BYS360_PHASE2C2Z_SAFE_SUBSET_FINAL_VERIFY.md"

TARGET_FILES = [
    "app/api/mobile/domains/assistant_chat.py",
    "app/api/mobile/domains/auth.py",
    "app/api/mobile/domains/communication_v1_write.py",
    "app/api/mobile/domains/communication_v2_write.py",
    "app/api/mobile/domains/dashboard.py",
    "app/api/mobile/domains/kpi_target_management.py",
    "app/api/mobile/domains/notifications.py",
    "app/api/mobile/domains/personnel_read.py",
    "app/api/mobile/domains/personnel_write_all.py",
    "app/api/mobile/domains/support_survey_write.py",
]

INTENTIONAL_SKIP_FILE = "app/api/mobile/routes.py"


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
            "combined_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-30000:],
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
            "combined_tail": (stdout + "\n" + stderr + "\nTIMEOUT")[-30000:],
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


def ast_wildcard_imports_under_app() -> list[dict]:
    rows = []

    for path in sorted((ROOT / "app").rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        try:
            tree = ast.parse(read_text(path), filename=str(path))
        except Exception as exc:
            rows.append({
                "file": rel,
                "line_no": None,
                "module": None,
                "error": str(exc),
            })
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                names = [alias.name for alias in node.names]
                if "*" in names:
                    rows.append({
                        "file": rel,
                        "line_no": node.lineno,
                        "module": node.module,
                        "level": node.level,
                    })

    return rows


def target_file_status() -> list[dict]:
    rows = []

    for rel in TARGET_FILES:
        path = ROOT / rel
        text = read_text(path)

        has_shared_wildcard = bool(re.search(
            r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+\*\s*(?:#.*)?$",
            text,
            flags=re.MULTILINE,
        ))

        explicit_shared_imports = re.findall(
            r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+(.+)$",
            text,
            flags=re.MULTILINE,
        )

        rows.append({
            "file": rel,
            "exists": path.exists(),
            "has_shared_wildcard": has_shared_wildcard,
            "explicit_shared_import_lines": explicit_shared_imports,
            "ok": path.exists() and not has_shared_wildcard and bool(explicit_shared_imports),
        })

    return rows


def skipped_file_status() -> dict:
    path = ROOT / INTENTIONAL_SKIP_FILE
    text = read_text(path)

    has_shared_wildcard = bool(re.search(
        r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+\*\s*(?:#.*)?$",
        text,
        flags=re.MULTILINE,
    ))

    return {
        "file": INTENTIONAL_SKIP_FILE,
        "exists": path.exists(),
        "has_shared_wildcard": has_shared_wildcard,
        "reason": "Bilinçli facade import; ayrı refactor fazında ele alınacak.",
        "ok": path.exists() and has_shared_wildcard,
    }


def main() -> int:
    ARCH.mkdir(parents=True, exist_ok=True)

    py = ROOT / ".venv" / "Scripts" / "python.exe"

    wildcard_rows = ast_wildcard_imports_under_app()
    wildcard_by_module = Counter(str(row.get("module")) for row in wildcard_rows)
    wildcard_by_file = Counter(row["file"] for row in wildcard_rows)

    targets = target_file_status()
    skipped = skipped_file_status()

    compile_result = run_cmd([
        str(py), "-m", "compileall", "-q",
        "config.py", "app", "scripts", "tests", "migrations",
    ])

    contract_pytest = run_cmd([
        str(py), "-m", "pytest",
        "tests/architecture/test_phase2b_route_snapshot_contract.py",
        "-q", "-ra",
    ], timeout=900)

    quality_smoke = run_cmd([
        str(py), "-m", "pytest",
        "tests/quality",
        "-m", "ci_safe",
        "-q", "-ra",
    ], timeout=900)

    default_pytest = run_cmd([
        str(py), "-m", "pytest",
        "-m", "not live and not realdb and not slow",
        "-q", "-ra",
    ], timeout=1800)

    phase2c1_rerun = run_cmd([
        str(py),
        "scripts/quality/bys360_phase2c1_wildcard_import_explicit_plan.py",
    ], timeout=1800)

    contract_summary = parse_pytest_summary(contract_pytest["combined_tail"])
    quality_summary = parse_pytest_summary(quality_smoke["combined_tail"])
    default_summary = parse_pytest_summary(default_pytest["combined_tail"])

    target_all_ok = all(item["ok"] for item in targets)

    tests_green = (
        compile_result["returncode"] == 0
        and contract_pytest["returncode"] == 0
        and quality_smoke["returncode"] == 0
        and default_pytest["returncode"] == 0
        and contract_summary.get("failed", 0) == 0
        and contract_summary.get("errors", 0) == 0
        and default_summary.get("failed", 0) == 0
        and default_summary.get("errors", 0) == 0
        and default_summary.get("passed", 0) >= 700
    )

    app_mobile_shared_remaining = [
        row for row in wildcard_rows
        if row.get("module") == "app.api.mobile.shared"
    ]

    ok = (
        target_all_ok
        and skipped["ok"]
        and tests_green
        and len(app_mobile_shared_remaining) == 1
        and app_mobile_shared_remaining[0]["file"] == INTENTIONAL_SKIP_FILE
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "PHASE2C2Z_SAFE_SUBSET_FINAL_VERIFY",
        "mode": "verify_only_no_code_change",
        "ok": ok,
        "decision": "PHASE2C2Z_GREEN_MOBILE_SHARED_SAFE_SUBSET_CONFIRMED" if ok else "PHASE2C2Z_REVIEW_REQUIRED",
        "target_file_count": len(targets),
        "target_all_ok": target_all_ok,
        "target_status": targets,
        "intentional_skip": skipped,
        "app_ast_wildcard_import_count": len(wildcard_rows),
        "app_ast_wildcard_by_module_top_50": dict(wildcard_by_module.most_common(50)),
        "app_ast_wildcard_by_file_top_80": dict(wildcard_by_file.most_common(80)),
        "app_mobile_shared_remaining": app_mobile_shared_remaining,
        "compileall_returncode": compile_result["returncode"],
        "contract_pytest_returncode": contract_pytest["returncode"],
        "contract_pytest_summary": contract_summary,
        "quality_smoke_returncode": quality_smoke["returncode"],
        "quality_smoke_summary": quality_summary,
        "default_pytest_returncode": default_pytest["returncode"],
        "default_pytest_summary": default_summary,
        "phase2c1_rerun_returncode": phase2c1_rerun["returncode"],
        "phase2c1_tail": phase2c1_rerun["combined_tail"][-8000:],
        "tests_green": tests_green,
        "next_action": "Faz 2C3 ikinci güvenli wildcard import paketi planlanabilir." if ok else "Hedef dosya veya test kontrolü incelenmeli.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 Faz 2C2Z Safe Subset Final Verify",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Target file count: {result['target_file_count']}",
        f"- Target all OK: {result['target_all_ok']}",
        f"- Intentional skip OK: {result['intentional_skip']['ok']}",
        f"- App AST wildcard import count: {result['app_ast_wildcard_import_count']}",
        f"- App mobile shared remaining count: {len(result['app_mobile_shared_remaining'])}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Contract pytest returncode: {result['contract_pytest_returncode']}",
        f"- Quality smoke returncode: {result['quality_smoke_returncode']}",
        f"- Default pytest returncode: {result['default_pytest_returncode']}",
        f"- Tests green: {result['tests_green']}",
        "",
        "## Target Status",
        "",
        "```json",
        json.dumps(targets, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Intentional Skip",
        "",
        "```json",
        json.dumps(skipped, ensure_ascii=False, indent=2),
        "```",
        "",
        "## App Wildcard By Module Top 50",
        "",
        "```json",
        json.dumps(result["app_ast_wildcard_by_module_top_50"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## App Mobile Shared Remaining",
        "",
        "```json",
        json.dumps(app_mobile_shared_remaining, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Default Pytest Summary",
        "",
        "```json",
        json.dumps(default_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("PHASE2C2Z_REPORT_JSON:", OUT_JSON)
    print("PHASE2C2Z_REPORT_MD:", OUT_MD)
    print("PHASE2C2Z_TARGET_FILE_COUNT:", result["target_file_count"])
    print("PHASE2C2Z_TARGET_ALL_OK:", result["target_all_ok"])
    print("PHASE2C2Z_INTENTIONAL_SKIP_OK:", result["intentional_skip"]["ok"])
    print("PHASE2C2Z_APP_AST_WILDCARD_IMPORT_COUNT:", result["app_ast_wildcard_import_count"])
    print("PHASE2C2Z_APP_MOBILE_SHARED_REMAINING_COUNT:", len(result["app_mobile_shared_remaining"]))
    print("PHASE2C2Z_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("PHASE2C2Z_CONTRACT_PYTEST_RETURN_CODE:", result["contract_pytest_returncode"])
    print("PHASE2C2Z_QUALITY_SMOKE_RETURN_CODE:", result["quality_smoke_returncode"])
    print("PHASE2C2Z_DEFAULT_PYTEST_RETURN_CODE:", result["default_pytest_returncode"])
    print("PHASE2C2Z_DEFAULT_PYTEST_SUMMARY:", json.dumps(default_summary, ensure_ascii=False))
    print("PHASE2C2Z_PHASE2C1_RERUN_RETURN_CODE:", result["phase2c1_rerun_returncode"])
    print("PHASE2C2Z_TESTS_GREEN:", result["tests_green"])
    print("PHASE2C2Z_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
