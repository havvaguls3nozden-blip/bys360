from __future__ import annotations

import ast
import json
import re
from collections import Counter
from pathlib import Path

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
