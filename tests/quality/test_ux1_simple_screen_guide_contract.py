from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "app" / "templates" / "base.html"
JS = ROOT / "app" / "static" / "js" / "bys360_ux1_simple_screen_guide.js"
CSS = ROOT / "app" / "static" / "css" / "bys360_ux1_simple_screen_guide.css"


def test_ux1_assets_are_loaded_from_base_template():
    text = BASE.read_text(encoding="utf-8")
    assert "bys360_ux1_simple_screen_guide.css" in text
    assert "bys360_ux1_simple_screen_guide.js" in text
    assert "BYS360_UX1_SIMPLE_SCREEN_GUIDE_CSS" in text
    assert "BYS360_UX1_SIMPLE_SCREEN_GUIDE_JS" in text


def test_ux1_javascript_exports_contract_and_simplifies_long_text():
    text = JS.read_text(encoding="utf-8")
    assert "window.BYS360UX1SimpleScreenGuide" in text
    assert "resolveContext" in text
    assert "simplifyLongTextBlocks" in text
    assert "Detayı göster" in text
    assert "Kısa ekran mantığı" in text


def test_ux1_styles_define_quick_logic_and_collapsible_text():
    text = CSS.read_text(encoding="utf-8")
    assert ".bys360-ux1-quick-logic" in text
    assert ".bys360-ux1-long-text" in text
    assert ".bys360-ux1-steps" in text
    assert ".bys360-ux1-action-focus" in text
