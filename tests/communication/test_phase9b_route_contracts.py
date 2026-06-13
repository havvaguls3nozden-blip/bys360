from pathlib import Path
import ast


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMM_ROOT = PROJECT_ROOT / 'app' / 'communication'


def _collect_routes(path: Path) -> set[str]:
    source = path.read_text(encoding='utf-8')
    tree = ast.parse(source)
    routes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'route' and node.args:
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                routes.add(first.value)
    return routes


def test_phase9b_routes_exist():
    routes = _collect_routes(COMM_ROOT / 'phase9b_routes.py')
    expected = {
        '/communication/faz9b',
        '/communication/faz9b/transition-center',
        '/communication/faz9b/gate',
        '/communication/faz9b/decision',
        '/communication/faz9b/export/md',
        '/communication/faz9b/export/json',
    }
    assert expected.issubset(routes)


def test_phase9b_templates_exist():
    for rel in [
        'app/templates/communication/phase9b_dashboard.html',
        'app/templates/communication/phase9b_transition_center.html',
    ]:
        assert (PROJECT_ROOT / rel).exists(), rel
