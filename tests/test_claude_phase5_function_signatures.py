"""
BYS360 Maintenance Faz 5 - Kritik fonksiyon imzası ve tanım testi.

Amaç: build_category_average_summary_for_users(period_id=...),
build_phase10_report_context(viewer=...) gibi çok noktadan çağrılan
fonksiyonların sessizce kırılmasını önlemek.

Marker: BYS360_MAINTENANCE_ROADMAP_PHASE5_FUNCTION_SIGNATURE_TEST
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "app"


EXPECTED_FUNCTIONS = {
    "build_category_average_summary_for_users": {"period_id"},
    "build_phase10_report_context": {"viewer"},
    "build_evaluation_flow_status": set(),
    "_build_assistant_role_matrix": set(),
}


def _discover_functions():
    found: dict[str, list[dict[str, Any]]] = {}
    if not APP_ROOT.exists():
        return found

    for py_file in sorted(APP_ROOT.rglob("*.py")):
        if any(part in {"__pycache__", ".pytest_cache"} for part in py_file.parts):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (tests/test_claude_phase5_function_signatures.py:41)")
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in node.args.args]
                kwonly = [a.arg for a in node.args.kwonlyargs]
                has_kwargs = node.args.kwarg is not None
                found.setdefault(node.name, []).append(
                    {
                        "file": str(py_file.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                        "args": args,
                        "kwonly": kwonly,
                        "has_kwargs": has_kwargs,
                    }
                )
    return found


@pytest.mark.parametrize("function_name,required_params", EXPECTED_FUNCTIONS.items())
def test_critical_function_exists_and_accepts_expected_parameters(function_name, required_params):
    found = _discover_functions()
    definitions = found.get(function_name, [])
    assert definitions, f"{function_name} tanımı app/ altında bulunamadı."

    if required_params:
        valid = []
        for item in definitions:
            accepted = set(item["args"]) | set(item["kwonly"])
            if item["has_kwargs"] or required_params.issubset(accepted):
                valid.append(item)
        assert valid, (
            f"{function_name} beklenen parametreleri kabul etmiyor. "
            f"Beklenen: {sorted(required_params)} | Bulunan: {definitions}"
        )
