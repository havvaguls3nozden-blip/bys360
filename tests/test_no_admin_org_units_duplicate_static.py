from pathlib import Path


def test_admin_org_units_registered_only_in_org_unit_routes():
    root = Path(__file__).resolve().parents[1]
    routes_py = root / "app" / "institutional" / "routes.py"
    org_routes_py = root / "app" / "institutional" / "org_unit_routes.py"

    routes_text = routes_py.read_text(encoding="utf-8")
    org_text = org_routes_py.read_text(encoding="utf-8")

    assert 'endpoint="admin_org_units"' not in routes_text
    assert 'main_bp.add_url_rule("/admin/org-units"' not in routes_text
    assert 'def admin_org_units' in org_text
    assert '@main_bp.route("/admin/org-units")' in org_text
