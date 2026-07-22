from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

QUALITY9_MAX_APP_PRINT = 0
DEFAULT_QUALITY9_MAX_APP_BROAD_EXCEPT = 2300
TARGET_KEYWORDS = ("auth", "session", "permission", "security")
SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", "backups", "backup",
    "reports", "logs", "releases", "overlays", "archive",
}


@dataclass
class GateFinding:
    code: str
    path: str
    detail: str
    line: int | None = None


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def iter_py(root: Path, base: Path) -> list[Path]:
    paths: list[Path] = []
    if base.is_file() and base.suffix == ".py":
        return [base]
    if not base.exists():
        return []
    for path in base.rglob("*.py"):
        try:
            parts = path.relative_to(root).parts
        except ValueError:
            parts = path.parts
        if any(part in SKIP_DIRS for part in parts):
            continue
        paths.append(path)
    return paths


def _is_exception_handler(node: ast.ExceptHandler) -> bool:
    if node.type is None:
        return False
    if isinstance(node.type, ast.Name) and node.type.id == "Exception":
        return True
    if isinstance(node.type, ast.Tuple):
        return any(isinstance(item, ast.Name) and item.id == "Exception" for item in node.type.elts)
    return False


def _uses_name(node: ast.AST, name: str) -> bool:
    return any(isinstance(child, ast.Name) and child.id == name for child in ast.walk(node))


def _has_logging_or_raise(node: ast.ExceptHandler) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Raise):
            return True
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Attribute) and func.attr in {"exception", "error", "warning", "critical", "info", "debug"}:
                return True
            if isinstance(func, ast.Name) and func.id.lower() in {"abort", "flash"}:
                return True
    return False


def scan_python(root: Path) -> tuple[dict[str, int], list[GateFinding]]:
    totals = {"python_files": 0, "syntax_errors": 0, "app_print_calls": 0, "app_broad_excepts": 0}
    findings: list[GateFinding] = []
    for path in iter_py(root, root / "app"):
        totals["python_files"] += 1
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        except SyntaxError as exc:
            totals["syntax_errors"] += 1
            findings.append(GateFinding("syntax_error", rel(path, root), exc.msg, exc.lineno))
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
                totals["app_print_calls"] += 1
            if isinstance(node, ast.ExceptHandler) and _is_exception_handler(node):
                totals["app_broad_excepts"] += 1
                if node.name is None and _uses_name(node, "exc"):
                    findings.append(GateFinding("undefined_exc_in_except", rel(path, root), "except bloğunda exc adı kullanılıyor ama yakalanmıyor", node.lineno))
                target_path = rel(path, root).lower()
                if any(keyword in target_path for keyword in TARGET_KEYWORDS) and not _has_logging_or_raise(node):
                    findings.append(GateFinding("silent_security_except", rel(path, root), "auth/session/permission/security hattında logsuz except Exception", node.lineno))
    return totals, findings


def check_workflow(root: Path, max_broad_except: int) -> list[GateFinding]:
    findings: list[GateFinding] = []
    path = root / ".github" / "workflows" / "bys360-ci.yml"
    if not path.exists():
        return [GateFinding("missing_ci_workflow", rel(path, root), "CI workflow bulunamadı")]
    text = path.read_text(encoding="utf-8", errors="ignore")
    normalized = text.replace("'", '"')
    accepted_pytest_commands = (
        'python -m pytest tests/quality -m "ci_safe" --tb=short -q',
        'python -m pytest tests/ -m "ci_safe" --tb=short -q',
    )
    if "name: Run tests" not in text or not any(cmd in normalized for cmd in accepted_pytest_commands):
        findings.append(GateFinding("pytest_not_enforced", rel(path, root), "CI içinde ci_safe pytest kapısı zorunlu"))
    if "--max-broad-except 3500" in text:
        findings.append(GateFinding("broad_except_threshold_too_loose", rel(path, root), "3500 eşiği kalite güvencesi üretmez"))
    match = re.search(r"--max-broad-except\s+(\d+)", text)
    if not match:
        findings.append(GateFinding("missing_broad_except_threshold", rel(path, root), "CI broad-except eşiği bulunamadı"))
    elif int(match.group(1)) > max_broad_except:
        findings.append(GateFinding("broad_except_threshold_above_quality9", rel(path, root), f"Eşik {match.group(1)}; kalite hedefi {max_broad_except}"))
    if "--source-paths app config.py wsgi.py run.py" not in text:
        findings.append(GateFinding("audit_scope_not_app", rel(path, root), "CI bütçesi yaşayan uygulama kodu için app/config/wsgi/run kapsamına bağlanmalı"))
    return findings


def check_ci_safe_hook(root: Path) -> list[GateFinding]:
    findings: list[GateFinding] = []
    path = root / "tests" / "conftest.py"
    if not path.exists():
        return [GateFinding("missing_tests_conftest", rel(path, root), "tests/conftest.py bulunamadı")]
    text = path.read_text(encoding="utf-8", errors="ignore")
    required = [
        "BYS360_QUALITY9_CI_SAFE_SCOPE_DISCIPLINE_START",
        "pytest_collection_modifyitems",
        "pytest_deselected",
        "tests/quality",
        "ci_safe",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        findings.append(GateFinding("ci_safe_scope_discipline_missing", rel(path, root), "Eksik parçalar: " + ", ".join(missing)))
    if "item.add_marker(ci_safe_marker)" in text:
        findings.append(GateFinding("ci_safe_scope_too_broad", rel(path, root), "Tüm testleri otomatik ci_safe işaretleyen eski davranış kapatılmalı"))
    quality_test = root / "tests" / "quality" / "test_quality9_ci_safe_contract.py"
    if not quality_test.exists():
        findings.append(GateFinding("missing_quality9_ci_safe_tests", rel(quality_test, root), "Deterministik ci_safe kalite testi bulunamadı"))
    return findings

def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 Quality 9 CI contract gate")
    parser.add_argument("--root", default=None)
    parser.add_argument("--project-root", dest="project_root", default=None, help="Backward-compatible alias for --root")
    parser.add_argument("--report", default="reports/quality/BYS360_QUALITY9_CI_GATE_REPORT.json")
    parser.add_argument("--max-broad-except", type=int, default=DEFAULT_QUALITY9_MAX_APP_BROAD_EXCEPT)
    args = parser.parse_args()

    root_value = args.root or args.project_root or "."
    root = Path(root_value).resolve()
    max_broad_except = int(args.max_broad_except)

    totals, findings = scan_python(root)
    findings.extend(check_workflow(root, max_broad_except))
    findings.extend(check_ci_safe_hook(root))

    if totals["syntax_errors"]:
        findings.append(GateFinding("syntax_errors_present", "app", f"Syntax hatası: {totals['syntax_errors']}"))
    if totals["app_print_calls"] > QUALITY9_MAX_APP_PRINT:
        findings.append(GateFinding("app_print_budget_exceeded", "app", f"print() {totals['app_print_calls']} > {QUALITY9_MAX_APP_PRINT}"))
    if totals["app_broad_excepts"] > max_broad_except:
        findings.append(GateFinding("app_broad_except_budget_exceeded", "app", f"except Exception {totals['app_broad_excepts']} > {max_broad_except}"))

    report = {
        "package": "BYS360_QUALITY9_CI_SAFE_SCOPE_HOTFIX_V10",
        "generated_at": datetime.now(UTC).isoformat(),
        "quality9_targets": {
            "app_print_calls_max": QUALITY9_MAX_APP_PRINT,
            "app_broad_except_max": max_broad_except,
            "ci_pytest_marker": "ci_safe",
            "security_silent_except_allowed": 0,
        },
        "totals": totals,
        "ok": not findings,
        "findings": [asdict(item) for item in findings],
    }
    report_path = Path(args.report)
    out = report_path if report_path.is_absolute() else root / report_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "totals": totals, "finding_count": len(findings), "report": str(out)}, ensure_ascii=False))
    if findings:
        for finding in findings[:30]:
            print(f"BYS360_QUALITY9_FAIL={finding.code} {finding.path}:{finding.line or ''} {finding.detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
