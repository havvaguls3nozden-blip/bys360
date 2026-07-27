from pathlib import Path

import pytest

pytestmark = pytest.mark.ci_safe

ROOT = Path(__file__).resolve().parents[2]


def test_ai_screen_guide_v2_static_contract():
    base = (ROOT / "app/templates/base.html").read_text(encoding="utf-8")
    js_path = ROOT / "app/static/js/bys360_ai_everywhere_v2.js"
    css_path = ROOT / "app/static/css/bys360_ai_everywhere_v2.css"
    assert "bys360_ai_everywhere_v2.js" in base
    assert "bys360_ai_everywhere_v2.css" in base
    assert "bys360_ai_everywhere_v1.js" not in base
    assert "bys360_ai_everywhere_v1.css" not in base
    js = js_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")
    assert "window.BYS360AIEverywhereV2" in js
    assert "renderInlineAnswer" in js
    assert "data-ai-everywhere-answer" in js
    assert "window.BYS360AssistantModule.open" in js
    assert ".bys360-ai-everywhere-answer" in css
