from pathlib import Path


def test_feedback_admin_pulse_endpoint_is_registered_separately():
    text = Path('app/communication/feedback_routes.py').read_text(encoding='utf-8')
    assert "@main_bp.route('/feedback/admin/pulse-analytics')" in text
    assert 'def feedback_admin_pulse_analytics()' in text
    assert 'def feedback_pulse_analytics()' in text
    assert 'def _render_feedback_pulse_analytics()' in text
    assert 'return _render_feedback_pulse_analytics()' in text
