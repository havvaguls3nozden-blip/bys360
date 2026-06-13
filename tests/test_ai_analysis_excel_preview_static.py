from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_faz7_excel_preview_has_no_import_contract():
    service = read("app/services/ai/excel_preview.py")
    assert "GERCEK_ICE_AKTARIM_YOK = True" in service
    assert "DB_WRITE_ENABLED = False" in service
    assert "validate_upload" in service
    assert "ALLOWED_ANALYSIS_EXTENSIONS" in service
    assert "mask_cell_value" in service
    assert "db.session" not in service
    assert ".save(" not in service


def test_faz7_excel_preview_route_is_admin_ai_scoped():
    route = read("app/admin/ai_phase7_routes.py")
    assert "/admin/analysis-center/excel-preview" in route
    assert "methods=['GET', 'POST']" in route
    assert "@admin_required" in route
    assert "@menu_key_required('ai_center')" in route
    assert "build_safe_excel_preview" in route


def test_faz7_excel_preview_template_says_no_real_import_and_kvkk():
    template = read("app/templates/admin_analysis_excel_preview.html")
    assert "Gerçek içe aktarım" in template
    assert "KVKK" in template
    assert "Örnek satır" in template
    assert "csrf_token()" in template


def test_ai_center_links_to_faz7_preview():
    center = read("app/templates/admin_ai_center.html")
    assert "main.admin_analysis_center_excel_preview" in center
    assert "Excel önizleme" in center
