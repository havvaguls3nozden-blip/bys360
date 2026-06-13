from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter
import ast
import builtins
import json
import os
import re
import subprocess

ROOT = Path(".").resolve()
ARCH = ROOT / "reports" / "architecture"

OUT_JSON = ARCH / "BYS360_PHASE2C1_WILDCARD_IMPORT_EXPLICIT_PLAN.json"
OUT_MD = ARCH / "BYS360_PHASE2C1_WILDCARD_IMPORT_EXPLICIT_PLAN.md"

EXCLUDED_DIR_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "reports",
    "releases",
    "archive",
    "backups",
}

BUILTIN_NAMES = set(dir(builtins))


def should_skip(path: Path) -> bool:
    rel_parts = path.relative_to(ROOT).parts
    lowered = {part.lower() for part in rel_parts}
    return bool(EXCLUDED_DIR_PARTS & lowered)


def py_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*.py"):
        if should_skip(path):
            continue
        files.append(path)
    return sorted(files)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


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
    except FileNotFoundError as exc:
        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": 127,
            "stdout": "",
            "stderr": str(exc),
            "combined_tail": str(exc)[-30000:],
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


def ast_parse(path: Path):
    try:
        return ast.parse(read_text(path), filename=str(path))
    except Exception as exc:
        return exc


def module_to_path(module: str | None, level: int, importer_file: Path) -> Path | None:
    if level and level > 0:
        base = importer_file.parent
        for _ in range(level - 1):
            base = base.parent
        if module:
            parts = module.split(".")
            candidate = base.joinpath(*parts)
        else:
            candidate = base

        py_candidate = candidate.with_suffix(".py")
        init_candidate = candidate / "__init__.py"

        if py_candidate.exists():
            return py_candidate
        if init_candidate.exists():
            return init_candidate
        return None

    if not module:
        return None

    candidate = ROOT / Path(*module.split("."))
    py_candidate = candidate.with_suffix(".py")
    init_candidate = candidate / "__init__.py"

    if py_candidate.exists():
        return py_candidate
    if init_candidate.exists():
        return init_candidate

    return None


def find_wildcard_imports(files: list[Path]) -> list[dict]:
    rows = []

    for path in files:
        tree = ast_parse(path)
        if not isinstance(tree, ast.Module):
            continue

        rel = path.relative_to(ROOT).as_posix()

        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue

            names = [alias.name for alias in node.names]
            if "*" not in names:
                continue

            resolved = module_to_path(node.module, node.level, path)

            rows.append({
                "file": rel,
                "line_no": node.lineno,
                "module": node.module,
                "level": node.level,
                "resolved_module_path": (
                    resolved.relative_to(ROOT).as_posix()
                    if resolved and resolved.exists()
                    else None
                ),
            })

    return rows


def exported_names_from_module(module_path: Path | None) -> dict:
    if module_path is None or not module_path.exists():
        return {
            "resolved": False,
            "export_names": [],
            "source": "module_not_resolved",
        }

    tree = ast_parse(module_path)
    if not isinstance(tree, ast.Module):
        return {
            "resolved": False,
            "export_names": [],
            "source": "module_parse_failed",
        }

    explicit_all = []

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    try:
                        value = ast.literal_eval(node.value)
                        if isinstance(value, (list, tuple, set)):
                            explicit_all = [
                                str(item) for item in value
                                if isinstance(item, str)
                            ]
                    except Exception:
                        explicit_all = []

    if explicit_all:
        return {
            "resolved": True,
            "export_names": sorted(set(explicit_all)),
            "source": "__all__",
        }

    names = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                names.append(node.name)

        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    names.append(target.id)

        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and not target.id.startswith("_"):
                names.append(target.id)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                if not name.startswith("_"):
                    names.append(name)

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    continue
                name = alias.asname or alias.name
                if not name.startswith("_"):
                    names.append(name)

    return {
        "resolved": True,
        "export_names": sorted(set(names)),
        "source": "top_level_public_names",
    }


def names_defined_in_consumer(tree: ast.Module) -> set[str]:
    defined = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                defined.add(alias.asname or alias.name.split(".")[0])

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    defined.add(alias.asname or alias.name)

        elif isinstance(node, ast.arg):
            defined.add(node.arg)

        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            defined.add(node.id)

    return defined


def names_loaded_in_consumer(tree: ast.Module) -> set[str]:
    loaded = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            loaded.add(node.id)

    return loaded


def build_plan_item(row: dict) -> dict:
    importer = ROOT / row["file"]
    module_path = ROOT / row["resolved_module_path"] if row["resolved_module_path"] else None

    export_info = exported_names_from_module(module_path)

    tree = ast_parse(importer)
    if not isinstance(tree, ast.Module):
        return {
            **row,
            "status": "manual_review",
            "reason": "consumer_parse_failed",
            "export_source": export_info["source"],
            "export_count": len(export_info["export_names"]),
            "used_export_names": [],
            "suggested_import_line": None,
            "risk": "high",
        }

    loaded = names_loaded_in_consumer(tree)
    defined = names_defined_in_consumer(tree)

    export_names = set(export_info["export_names"])
    used_export_names = sorted(
        name for name in (loaded & export_names)
        if name not in BUILTIN_NAMES
    )

    if not export_info["resolved"]:
        status = "manual_review"
        reason = export_info["source"]
        risk = "high"
    elif not used_export_names:
        status = "manual_review"
        reason = "no_used_export_name_detected"
        risk = "medium"
    elif len(used_export_names) > 40:
        status = "manual_review"
        reason = "too_many_names_for_safe_auto_plan"
        risk = "medium"
    else:
        status = "ready_for_explicit_import"
        reason = "used_names_detected"
        risk = "low" if len(used_export_names) <= 20 else "medium"

    module_expr = "." * int(row["level"]) + (row["module"] or "")
    suggested = (
        f"from {module_expr} import {', '.join(used_export_names)}"
        if used_export_names else None
    )

    possible_shadowed_names = sorted(set(used_export_names) & defined)

    return {
        **row,
        "status": status,
        "reason": reason,
        "risk": risk,
        "export_source": export_info["source"],
        "export_count": len(export_info["export_names"]),
        "used_export_count": len(used_export_names),
        "used_export_names": used_export_names,
        "possible_shadowed_names": possible_shadowed_names,
        "suggested_import_line": suggested,
    }


def main() -> int:
    ARCH.mkdir(parents=True, exist_ok=True)

    files = py_files()
    wildcard_rows = find_wildcard_imports(files)
    plan_items = [build_plan_item(row) for row in wildcard_rows]

    by_status = Counter(item["status"] for item in plan_items)
    by_risk = Counter(item["risk"] for item in plan_items)
    by_module = Counter(str(item.get("module")) for item in plan_items)
    ready_items = [item for item in plan_items if item["status"] == "ready_for_explicit_import"]

    py = ROOT / ".venv" / "Scripts" / "python.exe"

    compile_result = run_cmd([
        str(py),
        "-m",
        "compileall",
        "-q",
        "config.py",
        "app",
        "scripts",
        "tests",
        "migrations",
    ])

    contract_pytest = run_cmd([
        str(py),
        "-m",
        "pytest",
        "tests/architecture/test_phase2b_route_snapshot_contract.py",
        "-q",
        "-ra",
    ], timeout=900)

    default_pytest = run_cmd([
        str(py),
        "-m",
        "pytest",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
    ], timeout=1800)

    contract_summary = parse_pytest_summary(contract_pytest["combined_tail"])
    default_summary = parse_pytest_summary(default_pytest["combined_tail"])

    ok = (
        len(wildcard_rows) > 0
        and compile_result["returncode"] == 0
        and contract_pytest["returncode"] == 0
        and default_pytest["returncode"] == 0
        and default_summary.get("failed", 0) == 0
        and default_summary.get("errors", 0) == 0
        and default_summary.get("passed", 0) >= 700
    )

    first_apply_candidates = [
        item for item in ready_items
        if (
            item["risk"] == "low"
            and item["resolved_module_path"]
            and item["file"].startswith("app/api/mobile/")
            and item["module"] == "app.api.mobile.shared"
        )
    ][:12]

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "PHASE2C1_WILDCARD_IMPORT_EXPLICIT_PLAN",
        "mode": "plan_only_no_code_change",
        "ok": ok,
        "decision": "PHASE2C1_PLAN_READY" if ok else "PHASE2C1_REVIEW_REQUIRED",
        "wildcard_import_count": len(wildcard_rows),
        "ready_for_explicit_import_count": len(ready_items),
        "manual_review_count": by_status.get("manual_review", 0),
        "by_status": dict(by_status),
        "by_risk": dict(by_risk),
        "by_module_top_50": dict(by_module.most_common(50)),
        "first_apply_candidate_count": len(first_apply_candidates),
        "first_apply_candidates": first_apply_candidates,
        "plan_items": plan_items,
        "compileall_returncode": compile_result["returncode"],
        "contract_pytest_returncode": contract_pytest["returncode"],
        "contract_pytest_summary": contract_summary,
        "pytest_default_returncode": default_pytest["returncode"],
        "pytest_default_summary": default_summary,
        "next_action": "Faz 2C2 düşük riskli app/api/mobile/shared wildcard import dönüşümü uygulanabilir." if ok and first_apply_candidates else "Faz 2C1 raporu incelenmeli.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 Faz 2C1 Wildcard Import Explicit Plan",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Wildcard import count: {result['wildcard_import_count']}",
        f"- Ready for explicit import count: {result['ready_for_explicit_import_count']}",
        f"- Manual review count: {result['manual_review_count']}",
        f"- First apply candidate count: {result['first_apply_candidate_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Contract pytest returncode: {result['contract_pytest_returncode']}",
        f"- Pytest default returncode: {result['pytest_default_returncode']}",
        "",
        "## By Status",
        "",
        "```json",
        json.dumps(result["by_status"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## By Risk",
        "",
        "```json",
        json.dumps(result["by_risk"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## By Module Top 50",
        "",
        "```json",
        json.dumps(result["by_module_top_50"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## First Apply Candidates",
        "",
        "```json",
        json.dumps(first_apply_candidates, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Manual Review Items Top 80",
        "",
        "```json",
        json.dumps([item for item in plan_items if item["status"] == "manual_review"][:80], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Contract Pytest Summary",
        "",
        "```json",
        json.dumps(contract_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Default Summary",
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

    print("PHASE2C1_REPORT_JSON:", OUT_JSON)
    print("PHASE2C1_REPORT_MD:", OUT_MD)
    print("PHASE2C1_WILDCARD_IMPORT_COUNT:", result["wildcard_import_count"])
    print("PHASE2C1_READY_FOR_EXPLICIT_IMPORT_COUNT:", result["ready_for_explicit_import_count"])
    print("PHASE2C1_MANUAL_REVIEW_COUNT:", result["manual_review_count"])
    print("PHASE2C1_BY_STATUS:", json.dumps(result["by_status"], ensure_ascii=False))
    print("PHASE2C1_BY_RISK:", json.dumps(result["by_risk"], ensure_ascii=False))
    print("PHASE2C1_FIRST_APPLY_CANDIDATE_COUNT:", result["first_apply_candidate_count"])
    print("PHASE2C1_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("PHASE2C1_CONTRACT_PYTEST_RETURN_CODE:", result["contract_pytest_returncode"])
    print("PHASE2C1_CONTRACT_PYTEST_SUMMARY:", json.dumps(contract_summary, ensure_ascii=False))
    print("PHASE2C1_PYTEST_DEFAULT_RETURN_CODE:", result["pytest_default_returncode"])
    print("PHASE2C1_PYTEST_DEFAULT_SUMMARY:", json.dumps(default_summary, ensure_ascii=False))
    print("PHASE2C1_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
