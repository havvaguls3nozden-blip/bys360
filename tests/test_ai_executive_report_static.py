from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase11_contract_is_read_only_and_safe():
    service = (ROOT / "app/services/ai/executive_report_exports.py").read_text(encoding="utf-8")
    assert "DB_WRITE_ENABLED = False" in service
    assert "RAW_AI_PAYLOAD_EXPORT_ENABLED = False" in service
    assert "PERSONAL_DATA_EXPORT_ENABLED = False" in service
    assert "REAL_IMPORT_ENABLED = False" in service
    assert "db.session.commit" not in service
    assert "db.session.add" not in service


def test_phase11_routes_and_template_exist():
    route = (ROOT / "app/admin/ai_phase11_routes.py").read_text(encoding="utf-8")
    template = (ROOT / "app/templates/admin_ai_executive_report.html").read_text(encoding="utf-8")
    assert "/admin/analysis-center/executive-report" in route
    assert "admin_ai_executive_report_export_csv" in route
    assert "AI Yönetici Rapor ve Export Merkezi" in template
    assert "Ham AI metni" in template
