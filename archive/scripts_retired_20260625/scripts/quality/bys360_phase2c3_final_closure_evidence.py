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

OUT_JSON = ARCH / "BYS360_PHASE2C3_FINAL_CLOSURE_EVIDENCE.json"
OUT_MD = ARCH / "BYS360_PHASE2C3_FINAL_CLOSURE_EVIDENCE.md"

EXPECTED_EXPLICIT_FILES = [
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

EXPECTED_REMAINING_WILDCARD_FILES = [
    "app/api/mobile/routes.py",
]


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
        "combined_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-30000:],
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


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8-sig", errors="ignore")


def has_mobile_shared_wildcard(rel: str) -> bool:
    return bool(re.search(
        r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+\*\s*(?:#.*)?$",
        read_text(rel),
        flags=re.MULTILINE,
    ))


def has_mobile_shared_explicit(rel: str) -> bool:
    return bool(re.search(
        r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+(?!\*)",
        read_text(rel),
        flags=re.MULTILINE,
    ))


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

    explicit_status = [
        {
            "file": rel,
            "has_mobile_shared_wildcard": has_mobile_shared_wildcard(rel),
            "has_mobile_shared_explicit": has_mobile_shared_explicit(rel),
            "ok": (not has_mobile_shared_wildcard(rel)) and has_mobile_shared_explicit(rel),
        }
        for rel in EXPECTED_EXPLICIT_FILES
    ]

    remaining_status = [
        {
            "file": rel,
            "has_mobile_shared_wildcard": has_mobile_shared_wildcard(rel),
            "has_mobile_shared_explicit": has_mobile_shared_explicit(rel),
            "ok": has_mobile_shared_wildcard(rel),
            "reason": "Bilinçli facade import; C4'te ayrı değerlendirilecek.",
        }
        for rel in EXPECTED_REMAINING_WILDCARD_FILES
    ]

    wildcard_rows = app_wildcards()
    by_module = Counter(str(row.get("module")) for row in wildcard_rows)

    mobile_shared_remaining = [
        row for row in wildcard_rows
        if row.get("module") == "app.api.mobile.shared"
    ]

    py = ROOT / ".venv" / "Scripts" / "python.exe"

    compile_result = run_cmd([
        str(py), "-m", "compileall", "-q",
        "config.py", "app", "scripts", "tests", "migrations",
    ])

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

    phase2c1 = run_cmd([
        str(py),
        "scripts/quality/bys360_phase2c1_wildcard_import_explicit_plan.py",
    ], timeout=1800)

    contract_summary = parse_pytest_summary(contract["combined_tail"])
    auth_guard_summary = parse_pytest_summary(auth_guard["combined_tail"])
    default_summary = parse_pytest_summary(default["combined_tail"])

    tests_green = (
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

    explicit_ok = all(item["ok"] for item in explicit_status)
    remaining_ok = all(item["ok"] for item in remaining_status)

    ok = (
        explicit_ok
        and remaining_ok
        and len(mobile_shared_remaining) == 1
        and mobile_shared_remaining[0]["file"] == "app/api/mobile/routes.py"
        and tests_green
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "PHASE2C3_FINAL_CLOSURE_EVIDENCE",
        "ok": ok,
        "decision": "PHASE2C3_GREEN_CLOSED_AUTH_IMPORT_APPLIED" if ok else "PHASE2C3_REVIEW_REQUIRED",
        "explicit_expected_count": len(EXPECTED_EXPLICIT_FILES),
        "explicit_ok": explicit_ok,
        "explicit_status": explicit_status,
        "remaining_wildcard_expected_count": len(EXPECTED_REMAINING_WILDCARD_FILES),
        "remaining_wildcard_ok": remaining_ok,
        "remaining_wildcard_status": remaining_status,
        "app_ast_wildcard_count": len(wildcard_rows),
        "app_ast_wildcard_by_module_top_50": dict(by_module.most_common(50)),
        "mobile_shared_remaining": mobile_shared_remaining,
        "compileall_returncode": compile_result["returncode"],
        "contract_pytest_returncode": contract["returncode"],
        "contract_pytest_summary": contract_summary,
        "auth_guard_pytest_returncode": auth_guard["returncode"],
        "auth_guard_pytest_summary": auth_guard_summary,
        "default_pytest_returncode": default["returncode"],
        "default_pytest_summary": default_summary,
        "phase2c1_rerun_returncode": phase2c1["returncode"],
        "tests_green": tests_green,
        "next_action": "Faz 2C4: app/api/mobile/routes.py bilinçli facade import ayrı ve yedekli full-gate ile değerlendirilebilir." if ok else "Hedef dosyalar veya test kapıları incelenmeli.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 Faz 2C3 Final Closure Evidence",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Explicit expected count: {result['explicit_expected_count']}",
        f"- Explicit OK: {result['explicit_ok']}",
        f"- Remaining wildcard expected count: {result['remaining_wildcard_expected_count']}",
        f"- Remaining wildcard OK: {result['remaining_wildcard_ok']}",
        f"- App AST wildcard count: {result['app_ast_wildcard_count']}",
        f"- Mobile shared remaining count: {len(result['mobile_shared_remaining'])}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Contract pytest returncode: {result['contract_pytest_returncode']}",
        f"- Auth guard pytest returncode: {result['auth_guard_pytest_returncode']}",
        f"- Default pytest returncode: {result['default_pytest_returncode']}",
        f"- Tests green: {result['tests_green']}",
        "",
        "## Explicit Status",
        "",
        "```json",
        json.dumps(explicit_status, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Remaining Wildcard Status",
        "",
        "```json",
        json.dumps(remaining_status, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Mobile Shared Remaining",
        "",
        "```json",
        json.dumps(mobile_shared_remaining, ensure_ascii=False, indent=2),
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

    print("PHASE2C3_FINAL_REPORT_JSON:", OUT_JSON)
    print("PHASE2C3_FINAL_REPORT_MD:", OUT_MD)
    print("PHASE2C3_FINAL_EXPLICIT_OK:", result["explicit_ok"])
    print("PHASE2C3_FINAL_REMAINING_WILDCARD_OK:", result["remaining_wildcard_ok"])
    print("PHASE2C3_FINAL_APP_AST_WILDCARD_COUNT:", result["app_ast_wildcard_count"])
    print("PHASE2C3_FINAL_MOBILE_SHARED_REMAINING_COUNT:", len(result["mobile_shared_remaining"]))
    print("PHASE2C3_FINAL_CONTRACT_RETURN_CODE:", result["contract_pytest_returncode"])
    print("PHASE2C3_FINAL_AUTH_GUARD_RETURN_CODE:", result["auth_guard_pytest_returncode"])
    print("PHASE2C3_FINAL_DEFAULT_RETURN_CODE:", result["default_pytest_returncode"])
    print("PHASE2C3_FINAL_DEFAULT_SUMMARY:", json.dumps(default_summary, ensure_ascii=False))
    print("PHASE2C3_FINAL_TESTS_GREEN:", result["tests_green"])
    print("PHASE2C3_FINAL_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
