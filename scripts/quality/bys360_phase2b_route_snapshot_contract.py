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
TEST_DIR = ROOT / "tests" / "architecture"
SNAPSHOT_DIR = TEST_DIR / "snapshots"

OUT_JSON = ARCH / "BYS360_PHASE2B_ROUTE_SNAPSHOT_CONTRACT.json"
OUT_MD = ARCH / "BYS360_PHASE2B_ROUTE_SNAPSHOT_CONTRACT.md"
SNAPSHOT_JSON = SNAPSHOT_DIR / "phase2b_route_snapshot_baseline.json"
TEST_FILE = TEST_DIR / "test_phase2b_route_snapshot_contract.py"

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


def should_skip(path: Path) -> bool:
    rel_parts = path.relative_to(ROOT).parts
    lowered = {part.lower() for part in rel_parts}
    return bool(EXCLUDED_DIR_PARTS & lowered)


def app_py_files() -> list[Path]:
    base = ROOT / "app"
    if not base.exists():
        return []

    files = []
    for path in base.rglob("*.py"):
        if should_skip(path):
            continue
        files.append(path)

    return sorted(files)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def dotted_name(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return dotted_name(node.func)
    return ""


def literal_or_repr(node) -> str | None:
    if isinstance(node, ast.Constant):
        if node.value is None:
            return None
        return str(node.value)
    try:
        return ast.unparse(node)
    except Exception:
        return None


def normalize_path(value: str | None) -> str:
    if not value:
        return "/"

    value = str(value).strip()

    if not value:
        return "/"

    if not value.startswith("/"):
        value = "/" + value

    value = re.sub(r"/+", "/", value)

    if len(value) > 1 and value.endswith("/"):
        value = value[:-1]

    return value


def combine_url(prefix: str | None, route_path: str | None) -> str:
    prefix_norm = "" if not prefix else normalize_path(prefix)
    route_norm = normalize_path(route_path)

    if prefix_norm in {"", "/"}:
        return route_norm

    if route_norm == "/":
        return prefix_norm

    return normalize_path(prefix_norm.rstrip("/") + "/" + route_norm.lstrip("/"))


def parse_methods_from_decorator(attr: str, call: ast.Call) -> list[str]:
    method_by_attr = {
        "get": ["GET"],
        "post": ["POST"],
        "put": ["PUT"],
        "patch": ["PATCH"],
        "delete": ["DELETE"],
    }

    if attr in method_by_attr:
        return method_by_attr[attr]

    methods = []

    for kw in call.keywords:
        if kw.arg != "methods":
            continue

        try:
            raw = ast.literal_eval(kw.value)
            if isinstance(raw, (list, tuple, set)):
                methods = [str(x).upper() for x in raw]
            elif isinstance(raw, str):
                methods = [raw.upper()]
        except Exception:
            maybe = literal_or_repr(kw.value)
            if maybe:
                methods = [maybe.upper()]

    if not methods:
        methods = ["GET"]

    return sorted(set(methods))


def ast_parse(path: Path):
    try:
        return ast.parse(read_text(path), filename=str(path))
    except Exception as exc:
        return exc


def build_snapshot() -> dict:
    routes = []
    blueprints = []

    for path in app_py_files():
        tree = ast_parse(path)
        if not isinstance(tree, ast.Module):
            continue

        rel = path.relative_to(ROOT).as_posix()
        blueprint_vars = {}

        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue

            if not isinstance(node.value, ast.Call):
                continue

            func_name = dotted_name(node.value.func)
            if not func_name.endswith("Blueprint"):
                continue

            bp_name = None
            url_prefix = None

            if node.value.args:
                bp_name = literal_or_repr(node.value.args[0])

            for kw in node.value.keywords:
                if kw.arg == "url_prefix":
                    url_prefix = literal_or_repr(kw.value)

            for target in node.targets:
                if isinstance(target, ast.Name):
                    blueprint_vars[target.id] = {
                        "var": target.id,
                        "name": bp_name,
                        "url_prefix": url_prefix,
                    }
                    blueprints.append({
                        "file": rel,
                        "line_no": node.lineno,
                        "var": target.id,
                        "name": bp_name,
                        "url_prefix": url_prefix,
                    })

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue

                if not isinstance(dec.func, ast.Attribute):
                    continue

                attr = dec.func.attr
                if attr not in {"route", "get", "post", "put", "patch", "delete"}:
                    continue

                owner = dotted_name(dec.func.value)
                route_path = literal_or_repr(dec.args[0]) if dec.args else "/"
                methods = parse_methods_from_decorator(attr, dec)

                bp_info = blueprint_vars.get(owner, {})
                bp_name = bp_info.get("name") or owner
                url_prefix = bp_info.get("url_prefix")

                full_path = combine_url(url_prefix, route_path)

                route = {
                    "contract_key": f"{full_path}|{','.join(methods)}",
                    "full_path": full_path,
                    "route_path": normalize_path(route_path),
                    "methods": methods,
                    "file": rel,
                    "line_no": node.lineno,
                    "function": node.name,
                    "decorator_owner": owner,
                    "blueprint_name": bp_name,
                    "url_prefix": url_prefix,
                }
                routes.append(route)

    routes = sorted(
        routes,
        key=lambda item: (
            item["contract_key"],
            item["blueprint_name"] or "",
            item["file"],
            item["function"],
            item["line_no"],
        ),
    )

    route_keys = [item["contract_key"] for item in routes]
    duplicate_keys = {
        key: count for key, count in Counter(route_keys).items()
        if count > 1
    }

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "phase2b_static_route_contract_baseline",
        "scan_root": "app",
        "route_count": len(routes),
        "blueprint_count": len(blueprints),
        "unique_contract_key_count": len(set(route_keys)),
        "duplicate_contract_keys": duplicate_keys,
        "contract_keys": route_keys,
        "routes": routes,
        "blueprints": blueprints,
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


TEST_CONTENT = r'''
from __future__ import annotations

from pathlib import Path
from collections import Counter
import ast
import json
import re

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_JSON = Path(__file__).resolve().parent / "snapshots" / "phase2b_route_snapshot_baseline.json"

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


def should_skip(path: Path) -> bool:
    rel_parts = path.relative_to(ROOT).parts
    lowered = {part.lower() for part in rel_parts}
    return bool(EXCLUDED_DIR_PARTS & lowered)


def app_py_files() -> list[Path]:
    base = ROOT / "app"
    return sorted(path for path in base.rglob("*.py") if not should_skip(path))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def dotted_name(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return dotted_name(node.func)
    return ""


def literal_or_repr(node) -> str | None:
    if isinstance(node, ast.Constant):
        if node.value is None:
            return None
        return str(node.value)
    try:
        return ast.unparse(node)
    except Exception:
        return None


def normalize_path(value: str | None) -> str:
    if not value:
        return "/"

    value = str(value).strip()

    if not value:
        return "/"

    if not value.startswith("/"):
        value = "/" + value

    value = re.sub(r"/+", "/", value)

    if len(value) > 1 and value.endswith("/"):
        value = value[:-1]

    return value


def combine_url(prefix: str | None, route_path: str | None) -> str:
    prefix_norm = "" if not prefix else normalize_path(prefix)
    route_norm = normalize_path(route_path)

    if prefix_norm in {"", "/"}:
        return route_norm

    if route_norm == "/":
        return prefix_norm

    return normalize_path(prefix_norm.rstrip("/") + "/" + route_norm.lstrip("/"))


def parse_methods_from_decorator(attr: str, call: ast.Call) -> list[str]:
    method_by_attr = {
        "get": ["GET"],
        "post": ["POST"],
        "put": ["PUT"],
        "patch": ["PATCH"],
        "delete": ["DELETE"],
    }

    if attr in method_by_attr:
        return method_by_attr[attr]

    methods = []

    for kw in call.keywords:
        if kw.arg != "methods":
            continue

        try:
            raw = ast.literal_eval(kw.value)
            if isinstance(raw, (list, tuple, set)):
                methods = [str(x).upper() for x in raw]
            elif isinstance(raw, str):
                methods = [raw.upper()]
        except Exception:
            maybe = literal_or_repr(kw.value)
            if maybe:
                methods = [maybe.upper()]

    if not methods:
        methods = ["GET"]

    return sorted(set(methods))


def build_contract_keys() -> list[str]:
    routes = []

    for path in app_py_files():
        try:
            tree = ast.parse(read_text(path), filename=str(path))
        except Exception:
            continue

        blueprint_vars = {}

        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue

            if not isinstance(node.value, ast.Call):
                continue

            if not dotted_name(node.value.func).endswith("Blueprint"):
                continue

            bp_name = None
            url_prefix = None

            if node.value.args:
                bp_name = literal_or_repr(node.value.args[0])

            for kw in node.value.keywords:
                if kw.arg == "url_prefix":
                    url_prefix = literal_or_repr(kw.value)

            for target in node.targets:
                if isinstance(target, ast.Name):
                    blueprint_vars[target.id] = {
                        "name": bp_name,
                        "url_prefix": url_prefix,
                    }

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue

                if not isinstance(dec.func, ast.Attribute):
                    continue

                attr = dec.func.attr
                if attr not in {"route", "get", "post", "put", "patch", "delete"}:
                    continue

                owner = dotted_name(dec.func.value)
                bp_info = blueprint_vars.get(owner, {})
                route_path = literal_or_repr(dec.args[0]) if dec.args else "/"
                methods = parse_methods_from_decorator(attr, dec)
                full_path = combine_url(bp_info.get("url_prefix"), route_path)

                routes.append(f"{full_path}|{','.join(methods)}")

    return sorted(routes)


def test_phase2b_route_contract_snapshot_is_stable():
    assert SNAPSHOT_JSON.exists(), f"Snapshot missing: {SNAPSHOT_JSON}"

    baseline = json.loads(SNAPSHOT_JSON.read_text(encoding="utf-8"))
    expected = sorted(baseline["contract_keys"])
    actual = build_contract_keys()

    expected_counter = Counter(expected)
    actual_counter = Counter(actual)

    missing = sorted((expected_counter - actual_counter).elements())
    added = sorted((actual_counter - expected_counter).elements())

    assert not missing and not added, {
        "message": "Route contract snapshot changed. Blueprint refactor must preserve route path/method contracts or update snapshot intentionally after review.",
        "expected_count": len(expected),
        "actual_count": len(actual),
        "missing_top_50": missing[:50],
        "added_top_50": added[:50],
    }


def test_phase2b_route_contract_has_expected_minimum_volume():
    baseline = json.loads(SNAPSHOT_JSON.read_text(encoding="utf-8"))
    actual = build_contract_keys()

    assert len(actual) == baseline["route_count"]
    assert len(actual) >= 900
'''


def main() -> int:
    ARCH.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    snapshot = build_snapshot()

    SNAPSHOT_JSON.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    TEST_FILE.write_text(TEST_CONTENT.strip() + "\n", encoding="utf-8")

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
        str(TEST_FILE),
        "-q",
        "-ra",
    ], timeout=900)

    quality_smoke = run_cmd([
        str(py),
        "-m",
        "pytest",
        "tests/quality",
        "-m",
        "ci_safe",
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
    quality_summary = parse_pytest_summary(quality_smoke["combined_tail"])
    default_summary = parse_pytest_summary(default_pytest["combined_tail"])

    ok = (
        snapshot["route_count"] >= 900
        and compile_result["returncode"] == 0
        and contract_pytest["returncode"] == 0
        and quality_smoke["returncode"] == 0
        and default_pytest["returncode"] == 0
        and contract_summary.get("failed", 0) == 0
        and contract_summary.get("errors", 0) == 0
        and default_summary.get("failed", 0) == 0
        and default_summary.get("errors", 0) == 0
        and default_summary.get("passed", 0) >= 700
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "PHASE2B_ROUTE_SNAPSHOT_CONTRACT",
        "mode": "add_snapshot_and_contract_tests_no_route_refactor",
        "ok": ok,
        "decision": "PHASE2B_ROUTE_CONTRACT_GREEN" if ok else "PHASE2B_REVIEW_REQUIRED",
        "snapshot_json": str(SNAPSHOT_JSON),
        "test_file": str(TEST_FILE),
        "route_count": snapshot["route_count"],
        "blueprint_count": snapshot["blueprint_count"],
        "unique_contract_key_count": snapshot["unique_contract_key_count"],
        "duplicate_contract_key_count": len(snapshot["duplicate_contract_keys"]),
        "duplicate_contract_keys_top_50": dict(list(snapshot["duplicate_contract_keys"].items())[:50]),
        "compileall_returncode": compile_result["returncode"],
        "contract_pytest_returncode": contract_pytest["returncode"],
        "contract_pytest_summary": contract_summary,
        "pytest_quality_smoke_returncode": quality_smoke["returncode"],
        "pytest_quality_smoke_summary": quality_summary,
        "pytest_default_returncode": default_pytest["returncode"],
        "pytest_default_summary": default_summary,
        "next_action": "Faz 2C wildcard import explicit import planına geçilebilir." if ok else "Phase2B raporu incelenmeli.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 Faz 2B Route Snapshot Contract",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Snapshot JSON: `{result['snapshot_json']}`",
        f"- Test file: `{result['test_file']}`",
        f"- Route count: {result['route_count']}",
        f"- Blueprint count: {result['blueprint_count']}",
        f"- Unique contract key count: {result['unique_contract_key_count']}",
        f"- Duplicate contract key count: {result['duplicate_contract_key_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Contract pytest returncode: {result['contract_pytest_returncode']}",
        f"- Pytest quality smoke returncode: {result['pytest_quality_smoke_returncode']}",
        f"- Pytest default returncode: {result['pytest_default_returncode']}",
        "",
        "## Duplicate Contract Keys Top 50",
        "",
        "```json",
        json.dumps(result["duplicate_contract_keys_top_50"], ensure_ascii=False, indent=2),
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

    print("PHASE2B_REPORT_JSON:", OUT_JSON)
    print("PHASE2B_REPORT_MD:", OUT_MD)
    print("PHASE2B_SNAPSHOT_JSON:", SNAPSHOT_JSON)
    print("PHASE2B_TEST_FILE:", TEST_FILE)
    print("PHASE2B_ROUTE_COUNT:", result["route_count"])
    print("PHASE2B_BLUEPRINT_COUNT:", result["blueprint_count"])
    print("PHASE2B_UNIQUE_CONTRACT_KEY_COUNT:", result["unique_contract_key_count"])
    print("PHASE2B_DUPLICATE_CONTRACT_KEY_COUNT:", result["duplicate_contract_key_count"])
    print("PHASE2B_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("PHASE2B_CONTRACT_PYTEST_RETURN_CODE:", result["contract_pytest_returncode"])
    print("PHASE2B_CONTRACT_PYTEST_SUMMARY:", json.dumps(contract_summary, ensure_ascii=False))
    print("PHASE2B_PYTEST_QUALITY_SMOKE_RETURN_CODE:", result["pytest_quality_smoke_returncode"])
    print("PHASE2B_PYTEST_DEFAULT_RETURN_CODE:", result["pytest_default_returncode"])
    print("PHASE2B_PYTEST_DEFAULT_SUMMARY:", json.dumps(default_summary, ensure_ascii=False))
    print("PHASE2B_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
