from pathlib import Path


def test_institutional_routes_does_not_register_admin_org_units_fallback_twice():
    text = Path("app/institutional/routes.py").read_text(encoding="utf-8")
    assert "main_bp.add_url_rule(\"/admin/org-units\"" not in text
    assert "@main_bp.route(\"/admin/org-units\", endpoint=\"admin_org_units\")" not in text
    assert "app.institutional.org_unit_routes" in text
