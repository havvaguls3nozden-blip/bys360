from pathlib import Path


def test_phase8_routes_file_exists():
    path = Path('app/communication/phase8_routes.py')
    assert path.exists()


def test_phase8_templates_exist():
    for rel in [
        'app/templates/communication/phase8_dashboard.html',
        'app/templates/communication/phase8_readiness_center.html',
        'app/templates/communication/phase8_cutover_center.html',
    ]:
        assert Path(rel).exists(), rel
