from pathlib import Path


def test_phase9c_routes_file_exists():
    assert Path('app/communication/phase9c_routes.py').exists()


def test_phase9c_templates_exist():
    for rel in [
        'app/templates/communication/phase9c_dashboard.html',
        'app/templates/communication/phase9c_pilot_opening_center.html',
    ]:
        assert Path(rel).exists(), rel
