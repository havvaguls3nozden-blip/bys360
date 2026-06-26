from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "app" / "templates" / "base.html"
JS = ROOT / "app" / "static" / "js" / "bys360_ux1_simple_screen_guide.js"
CSS = ROOT / "app" / "static" / "css" / "bys360_ux1_simple_screen_guide.css"


def test_ux1b_assets_are_loaded():
    text = BASE.read_text(encoding="utf-8")
    assert "bys360_ux1_simple_screen_guide.css" in text
    assert "bys360_ux1_simple_screen_guide.js" in text


def test_ux1b_js_ascii_safe_contract():
    text = JS.read_text(encoding="utf-8")
    assert "window.BYS360UX1SimpleScreenGuide" in text
    assert 'key: "performance"' in text
    assert 'key: "personnel"' in text
    assert "CONTEXTS" in text
    assert "simplifyLongTextBlocks" in text
    assert "bys360-ux1-more" in text
    assert "is-collapsed" in text


def test_ux1b_css_contract():
    text = CSS.read_text(encoding="utf-8")
    assert ".bys360-ux1-quick-logic" in text
    assert ".bys360-ux1-long-text" in text
    assert ".bys360-ux1-steps" in text
    assert ".bys360-ux1-action-focus" in text
