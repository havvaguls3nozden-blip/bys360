from pathlib import Path

import pytest

pytestmark = pytest.mark.ci_safe

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "app" / "templates" / "base.html"
JS = ROOT / "app" / "static" / "js" / "bys360_ux1_simple_screen_guide.js"
CSS = ROOT / "app" / "static" / "css" / "bys360_ux1_simple_screen_guide.css"


def test_ux1_top_banner_removed_but_simplifier_kept():
    base = BASE.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    assert "bys360_ux1_simple_screen_guide.js" in base
    assert "bys360_ux1_simple_screen_guide.css" in base
    assert "ux1-top-banner-remove-v1" in base

    assert "window.BYS360UX1SimpleScreenGuide" in js
    assert "topBannerEnabled: false" in js
    assert "removeGlobalQuickLogicCard" in js
    assert "data-ux1-toggle-details" not in js
    assert "data-ux1-ask-guide" not in js
    assert "bys360-ux1-steps" not in js

    assert "simplifyLongTextBlocks" in js
    assert "bys360-ux1-more" in js
    assert "is-collapsed" in js

    assert "BYS360_UX1_TOP_BANNER_REMOVE_V1" in css
    assert ".bys360-ux1-quick-logic" in css
    assert "display: none !important" in css
