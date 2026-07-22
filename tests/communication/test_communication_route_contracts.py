from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = PROJECT_ROOT / "app"
COMM_ROOT = APP_ROOT / "communication"


ROUTE_FILES = {
    "phase4_routes.py": {
        "/communication/faz4",
        "/communication/faz4/reports",
        "/communication/faz4/surveys/analytics",
        "/communication/faz4/support/analytics",
        "/communication/faz4/export-center",
        "/communication/faz4/export",
        "/communication/faz4/governance",
        "/communication/faz4/metrics/refresh",
    },
    "phase5_routes.py": {
        "/communication/faz5",
        "/communication/faz5/automation-center",
        "/communication/faz5/preferences",
        "/communication/faz5/escalations",
        "/communication/faz5/retention",
        "/communication/faz5/health",
        "/communication/faz5/audit-logs",
    },
    "feedback_routes.py": {
        "/feedback",
        "/feedback/pulse",
        "/feedback/campaigns",
        "/feedback/results",
        "/feedback/actions",
        "/feedback/manager",
        "/feedback/admin/campaigns",
    },
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _collect_route_literals(source: str) -> set[str]:
    routes: set[str] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        if func.attr != "route":
            continue
        if not node.args:
            continue
        first_arg = node.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            routes.add(first_arg.value)
    return routes


@pytest.mark.source_smoke
@pytest.mark.parametrize("filename, expected_routes", ROUTE_FILES.items())
def test_expected_routes_exist(filename: str, expected_routes: set[str]) -> None:
    path = COMM_ROOT / filename
    source = _read_text(path)
    routes = _collect_route_literals(source)
    missing = sorted(expected_routes - routes)
    assert not missing, f"Eksik route tanımları: {missing}"


@pytest.mark.source_smoke
def test_feedback_export_uses_utf8_sig() -> None:
    source = _read_text(COMM_ROOT / "feedback_routes.py")
    assert "charset=utf-8-sig" in source


@pytest.mark.source_smoke
def test_phase4_export_uses_utf8_sig() -> None:
    source = _read_text(COMM_ROOT / "phase4_routes.py")
    assert "utf-8-sig" in source


@pytest.mark.source_smoke
def test_no_direct_query_get_usage_in_communication_and_services() -> None:
    offenders: list[str] = []
    roots = [APP_ROOT / "communication", APP_ROOT / "services"]
    pattern = re.compile(r"\.query\.get\(")
    for root in roots:
        for path in root.rglob("*.py"):
            text = _read_text(path)
            if pattern.search(text):
                offenders.append(str(path.relative_to(PROJECT_ROOT)))
    assert offenders == [], f"query.get() kullanılan dosyalar bulundu: {offenders}"
