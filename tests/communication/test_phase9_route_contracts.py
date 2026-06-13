from __future__ import annotations

from pathlib import Path
import ast

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMM_ROOT = PROJECT_ROOT / 'app' / 'communication'
SERVICES_ROOT = PROJECT_ROOT / 'app' / 'services'


EXPECTED_ROUTES = {
    '/communication/faz9',
    '/communication/faz9/release-center',
    '/communication/faz9/first-72',
    '/communication/faz9/checkpoint',
    '/communication/faz9/decision',
    '/communication/faz9/export/md',
    '/communication/faz9/export/json',
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def _collect_route_literals(source: str) -> set[str]:
    routes: set[str] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        if func.attr != 'route':
            continue
        if not node.args:
            continue
        first_arg = node.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            routes.add(first_arg.value)
    return routes


@pytest.mark.source_smoke
def test_phase9_expected_routes_exist() -> None:
    source = _read_text(COMM_ROOT / 'phase9_routes.py')
    routes = _collect_route_literals(source)
    missing = sorted(EXPECTED_ROUTES - routes)
    assert not missing, f'Eksik Faz 9 route tanımları: {missing}'


@pytest.mark.source_smoke
def test_phase9_service_has_release_markdown_builder() -> None:
    source = _read_text(SERVICES_ROOT / 'communication_phase9_service.py')
    assert 'def build_phase9_release_markdown' in source
    assert 'def phase9_release_center_snapshot' in source
    assert 'phase9_checkpoint' in source
    assert 'phase9_decision' in source
