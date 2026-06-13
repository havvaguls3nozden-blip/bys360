from pathlib import Path


def test_phase9d_routes_file_exists():
    assert Path('app/communication/phase9d_routes.py').exists()


def test_phase9d_templates_exist():
    for rel in [
        'app/templates/communication/phase9d_dashboard.html',
        'app/templates/communication/phase9d_stabilization_center.html',
    ]:
        assert Path(rel).exists(), rel
