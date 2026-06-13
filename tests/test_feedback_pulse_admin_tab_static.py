from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_admin_pulse_analytics_route_exists():
    text = (ROOT / "app" / "communication" / "feedback_routes.py").read_text(encoding="utf-8")
    assert "def _render_feedback_pulse_analytics" in text
    assert "@main_bp.route('/feedback/admin/pulse-analytics')" in text
    assert "def feedback_admin_pulse_analytics" in text
    assert "@menu_key_required('feedback_admin')" in text


def test_base_has_separate_pulse_analysis_menu_item():
    text = (ROOT / "app" / "templates" / "base.html").read_text(encoding="utf-8")
    assert "Nabız Analizi" in text
    assert "main.feedback_admin_pulse_analytics" in text
    assert "main.feedback_pulse_analytics" in text
    assert "current_ep in ['main.feedback_pulse_analytics', 'main.feedback_admin_pulse_analytics']" in text


def test_feedback_core_menu_policy_contains_pulse_keys():
    text = (ROOT / "app" / "route_support.py").read_text(encoding="utf-8")
    assert '"feedback_pulse"' in text
    assert '"feedback_manager"' in text
    assert '"feedback_admin"' in text
    assert '"feedback_dashboard"' in text
