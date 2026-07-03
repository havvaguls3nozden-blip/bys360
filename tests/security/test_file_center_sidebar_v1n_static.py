from pathlib import Path


def test_file_center_sidebar_accordion_exists():
    base = Path("app/templates/base.html").read_text(encoding="utf-8")

    assert "BYS360_FILE_CENTER_SIDEBAR_V1N_BEGIN" in base
    assert "show_file_center_section" in base
    assert "data-accordion-key=\"dosya-merkezi\"" in base
    assert "Dosya Merkezi" in base
    assert "main.file_center_home" in base
    assert "main.file_center_transfers" in base
    assert "main.file_center_requests" in base
    assert "main.file_center_security" in base
    assert "main.file_center_settings" in base
    assert "main.file_center_role_matrix" in base


def test_file_center_routes_are_registered_from_main_routes():
    routes = Path("app/routes.py").read_text(encoding="utf-8")
    assert "from app.file_center import routes as _file_center_routes" in routes
