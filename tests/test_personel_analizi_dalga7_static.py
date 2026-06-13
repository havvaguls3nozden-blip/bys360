# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def test_personel_analizi_route_alias_and_export_name():
    text = read("app/performance/evaluation_core_routes.py")
    assert '@main_bp.route("/performance/personel-analizi")' in text
    assert 'build_period_download_name("personel_analizi"' in text
    assert '"<h3>Personel Analizi</h3>"' in text


def test_personel_analizi_template_and_menu_label():
    template = read("app/templates/team_compare.html")
    menu = read("app/menu_registry.py")
    assert "Personel Analizi - BYS360" in template
    assert '"label": "Personel Analizi"' in menu
    assert "Ekip Analizi" not in template
    assert "Ekip Kıyas" not in template


def test_personel_analizi_excel_sheet_name():
    service = read("app/services/performance/team_compare_service.py")
    assert 'sheet.title = "Personel Analizi"' in service
    assert "Ekip Analizi" not in service
