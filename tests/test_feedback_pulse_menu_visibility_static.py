from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_feedback_pulse_is_core_visible_for_all_roles():
    src = (ROOT / "app" / "route_support.py").read_text(encoding="utf-8")
    assert '"feedback_pulse": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"}' in src
    assert '("messages", "notifications", "surveys", "feedback_dashboard", "feedback_pulse")' in src


def test_feedback_pulse_menu_item_still_exists_in_base_and_registry():
    base = (ROOT / "app" / "templates" / "base.html").read_text(encoding="utf-8")
    registry = (ROOT / "app" / "menu_registry.py").read_text(encoding="utf-8")
    assert "menu_map.get('feedback_pulse'" in base
    assert "main.feedback_pulse" in base
    assert '"key": "feedback_pulse"' in registry
    assert '"endpoint": "main.feedback_pulse"' in registry
