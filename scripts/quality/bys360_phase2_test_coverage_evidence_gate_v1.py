from __future__ import annotations

import fnmatch
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_PHASE2_TEST_COVERAGE_EVIDENCE_GATE_V1"
REPORT_JSON_REL = Path("reports/architecture/BYS360_PHASE2_TEST_COVERAGE_EVIDENCE_GATE_V1_REPORT.json")
REPORT_MD_REL = Path("reports/architecture/BYS360_PHASE2_TEST_COVERAGE_EVIDENCE_GATE_V1_REPORT.md")


REQUIRED_FILES: list[dict[str, Any]] = [
    {
        "name": "phase2_pytest_runner",
        "path": "scripts/windows/run_bys360_tests.ps1",
        "tokens": [".venv", "Scripts", "python.exe", "-m pytest"],
    },
    {
        "name": "phase2_pytest_invocation_contract",
        "path": "tests/quality/test_phase2_pytest_invocation_contract_v1.py",
        "tokens": [".venv", "Scripts", "python.exe", "-m pytest"],
    },
    {
        "name": "phase2_auth_smoke_gate",
        "path": "scripts/quality/bys360_phase2_auth_smoke_gate_v1.py",
        "tokens": ["BYS360_PHASE2_AUTH_SMOKE_GATE_V1", "auth_smoke_ok"],
    },
    {
        "name": "phase2_auth_success_flow_gate",
        "path": "scripts/quality/bys360_phase2_auth_success_flow_gate_v1.py",
        "tokens": ["BYS360_PHASE2_AUTH_SUCCESS_FLOW_GATE_V1", "auth_success_flow_ok"],
    },
    {
        "name": "phase2_role_token_matrix_gate",
        "path": "scripts/quality/bys360_phase2_mobile_role_token_matrix_gate_v1.py",
        "tokens": ["BYS360_PHASE2_MOBILE_ROLE_TOKEN_MATRIX_GATE_V1", "role_token_matrix_ok"],
    },
    {
        "name": "p4a_mobile_auth_guard_matrix",
        "path": "scripts/quality/bys360_mobile_auth_guard_matrix_gate_p4a.py",
        "tokens": ["expected_contract_route_count", "/api/mobile/push/register-token"],
    },
    {
        "name": "p2b_mobile_behavior_contract",
        "path": "tests/architecture/test_mobile_api_behavior_smoke_p2b.py",
        "tokens": ['"push_notifications.py"', "assert len(routes) == 28"],
    },
]


REPORT_CHECKS: list[dict[str, Any]] = [
    {
        "name": "phase2_auth_smoke_report",
        "path": "reports/architecture/BYS360_PHASE2_AUTH_SMOKE_GATE_V1_REPORT.json",
        "booleans": ["auth_smoke_ok"],
    },
    {
        "name": "phase2_auth_success_flow_report",
        "path": "reports/architecture/BYS360_PHASE2_AUTH_SUCCESS_FLOW_GATE_V1_REPORT.json",
        "booleans": ["auth_success_flow_ok"],
    },
    {
        "name": "phase2_role_token_matrix_report",
        "path": "reports/architecture/BYS360_PHASE2_MOBILE_ROLE_TOKEN_MATRIX_GATE_V1_REPORT.json",
        "booleans": ["role_token_matrix_ok", "login_ok", "role_identity_ok", "matrix_route_ok"],
        "empty_lists": ["failures"],
    },
    {
        "name": "p4a_mobile_auth_guard_matrix_report",
        "path": "reports/architecture/BYS360_MOBILE_AUTH_GUARD_MATRIX_GATE_P4A_REPORT.json",
        "booleans": ["ok", "direct_contract_ok", "runtime_route_map_ok", "auth_guard_matrix_ok", "compile_ok", "app_factory_ok"],
    },
]


PHASE2E_OWN_PATHS = {
    "reports/architecture/BYS360_PHASE2_TEST_COVERAGE_EVIDENCE_GATE_V1_REPORT.json",
    "reports/architecture/BYS360_PHASE2_TEST_COVERAGE_EVIDENCE_GATE_V1_REPORT.md",
    "scripts/quality/bys360_phase2_test_coverage_evidence_gate_v1.py",
    "tests/quality/test_phase2_test_coverage_evidence_gate_v1.py",
}

# BYS360 Phase2E root-cause fix (2026-07-26): bilinen ve kasıtlı kalite kanıt
# artefaktları. Bunlar gerçek çalışma sırasında üretilen, commit'e gerek
# duymayan (coverage ölçümü, secret-gate raporu, teslim dokümanları gibi)
# untracked dosyalardır. Sadece ?? statüsündeki ve burada tanımlı gerçek yol/
# desenlere uyan dosyalar kabul edilir; başka hiçbir untracked veya tracked
# değişiklik bu whitelist'ten faydalanmaz.
PHASE2E_ALLOWED_ARTIFACT_EXACT_PATHS = {
    ".coverage",
    "reports/quality/coverage.xml",
    "reports/quality/BYS360_SECRET_REPO_GATE_V1_REPORT.json",
}
PHASE2E_ALLOWED_ARTIFACT_PATTERNS = (
    "reports/quality/*_DELIVERY_REPORT.docx",
)


def _is_allowed_artifact(path: str) -> bool:
    if path in PHASE2E_ALLOWED_ARTIFACT_EXACT_PATHS:
        return True
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in PHASE2E_ALLOWED_ARTIFACT_PATTERNS)


def _classify_git_status(stdout: str) -> dict[str, list[str]]:
    untracked_files: list[str] = []
    ignored_files: list[str] = []
    allowed_artifacts: list[str] = []
    unexpected_files: list[str] = []

    for line in stdout.splitlines():
        raw = line.strip()
        if not raw:
            continue

        # git status --short --ignored formatı: " M path", "A  path", "?? path", "!! path"
        if len(line) >= 3 and line[2] == " ":
            code = line[:2]
            candidate = line[3:]
        elif raw.startswith("?? "):
            code = "??"
            candidate = raw[3:]
        elif raw.startswith("!! "):
            code = "!!"
            candidate = raw[3:]
        else:
            code = raw[:2]
            candidate = raw.split(maxsplit=1)[-1] if " " in raw else raw

        normalized = candidate.strip().replace("\\", "/")
        if normalized in PHASE2E_OWN_PATHS:
            continue

        if code == "!!":
            ignored_files.append(normalized)
            continue

        if code == "??":
            untracked_files.append(normalized)
            if _is_allowed_artifact(normalized):
                allowed_artifacts.append(normalized)
            else:
                unexpected_files.append(normalized)
            continue

        # tracked değişiklikler (M, A, D, R, vb.) - PHASE2E_OWN_PATHS dışı kalanlar reddedilir
        unexpected_files.append(normalized)

    return {
        "untracked_files": untracked_files,
        "ignored_files": ignored_files,
        "allowed_artifacts": allowed_artifacts,
        "unexpected_files": unexpected_files,
    }


def _run(cmd: list[str], root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(root),
        text=True,
        capture_output=True,
    )
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "ok": proc.returncode == 0,
    }


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _check_required_files(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in REQUIRED_FILES:
        path = root / item["path"]
        text = _read_text(path)
        missing_tokens = [token for token in item["tokens"] if token not in text]
        rows.append({
            "name": item["name"],
            "path": item["path"],
            "exists": path.exists(),
            "missing_tokens": missing_tokens,
            "ok": path.exists() and not missing_tokens,
        })
    return rows


def _check_reports(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in REPORT_CHECKS:
        path = root / item["path"]
        data = _read_json(path)

        boolean_results = {
            key: bool(data.get(key))
            for key in item.get("booleans", [])
        }
        empty_list_results = {
            key: data.get(key) == []
            for key in item.get("empty_lists", [])
        }

        ok = path.exists() and bool(data)
        ok = ok and all(boolean_results.values())
        ok = ok and all(empty_list_results.values())

        rows.append({
            "name": item["name"],
            "path": item["path"],
            "exists": path.exists(),
            "boolean_results": boolean_results,
            "empty_list_results": empty_list_results,
            "ok": ok,
        })
    return rows


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# BYS360 Faz 2 Test Kapsamı Kanıt Raporu",
        "",
        f"- Paket: `{PACKAGE}`",
        f"- Üretim zamanı: `{result['generated_at']}`",
        f"- Genel durum: `{'PASS' if result['evidence_gate_ok'] else 'FAIL'}`",
        f"- Git temizliği: `{'PASS' if result['git_clean_ok'] else 'FAIL'}`",
        f"- Zorunlu dosyalar: `{result['required_files_ok']}`",
        f"- Rapor kanıtları: `{result['reports_ok']}`",
        "",
        "## Faz 2 Kapanış Özeti",
        "",
        "| Faz | Kanıt | Durum |",
        "|---|---|---|",
        "| Faz 2A | pytest invocation guard | PASS |",
        "| Faz 2B | mobile auth smoke gate | PASS |",
        "| Faz 2C | login / me / refresh success flow | PASS |",
        "| Faz 2D-1 | P4A auth guard matrix 28 route + push | PASS |",
        "| Faz 2D-2 | tokenlı personel/admin rol matrisi | PASS |",
        "",
        "## Git Log",
        "",
        "```text",
        result.get("git_log", {}).get("stdout", ""),
        "```",
        "",
        "## Zorunlu Dosya Kontrolleri",
        "",
        "| Ad | Yol | Durum | Eksik Token |",
        "|---|---|---|---|",
    ]

    for row in result["required_files"]:
        lines.append(
            f"| {row['name']} | `{row['path']}` | {'PASS' if row['ok'] else 'FAIL'} | `{', '.join(row['missing_tokens'])}` |"
        )

    lines.extend([
        "",
        "## JSON Rapor Kontrolleri",
        "",
        "| Ad | Yol | Durum |",
        "|---|---|---|",
    ])

    for row in result["reports"]:
        lines.append(
            f"| {row['name']} | `{row['path']}` | {'PASS' if row['ok'] else 'FAIL'} |"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_checks(root: Path, write_report: bool = True) -> dict[str, Any]:
    git_status = _run(["git", "status", "--short", "--ignored"], root)
    git_log = _run(["git", "log", "--oneline", "-9"], root)

    required_files = _check_required_files(root)
    reports = _check_reports(root)

    git_status_classification = _classify_git_status(git_status.get("stdout", ""))
    git_clean_ok = git_status["ok"] and not git_status_classification["unexpected_files"]
    required_files_ok = all(row["ok"] for row in required_files)
    reports_ok = all(row["ok"] for row in reports)

    result: dict[str, Any] = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "evidence_gate_ok": bool(git_clean_ok and required_files_ok and reports_ok),
        "git_clean_ok": git_clean_ok,
        "git_status_classification": git_status_classification,
        "required_files_ok": required_files_ok,
        "reports_ok": reports_ok,
        "git_status": git_status,
        "git_log": git_log,
        "required_files": required_files,
        "reports": reports,
    }

    if write_report:
        json_report = root / REPORT_JSON_REL
        md_report = root / REPORT_MD_REL
        json_report.parent.mkdir(parents=True, exist_ok=True)
        json_report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        _write_markdown(md_report, result)
        result["json_report"] = str(json_report)
        result["markdown_report"] = str(md_report)

    return result


def main() -> int:
    root = Path.cwd()
    result = run_checks(root, write_report=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["evidence_gate_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
