"""Phase 11B critical responsive screens - static contract gate.

Statik metin tabanlı kontrat testleri: gerçek tarayıcı/cihaz render'ı
doğrulamaz, yalnızca kaynak koddaki responsive/güvenlik/dil kurallarının
var olduğunu ve gerilemediğini denetler. Phase 11A'daki
test_phase11a_responsive_foundation_contract.py ile aynı desen.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_USER_FACING_TERMS = [
    "traceback",
    "exception",
    "endpoint",
    "workflow",
    "unauthorized_scope",
    "raw error",
]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


# --- Legacy approval screen touch-target safety (no route/template consolidation) ---


def test_foundation_css_covers_legacy_approval_buttons():
    css = text("app/static/css/bys360_responsive_foundation_v11a.css")
    assert ".wf-btn" in css
    assert ".pa-btn" in css  # canonical screen coverage from Phase 11A must not regress


def test_legacy_approval_action_buttons_use_wf_btn_class():
    template = text("app/templates/workflow/president_approvals.html")
    assert 'btn btn-sm btn-success wf-btn" name="action" value="APPROVE"' in template
    assert 'btn btn-sm btn-warning wf-btn" name="action" value="RETURN"' in template
    assert 'btn btn-sm btn-outline-danger wf-btn" name="action" value="REJECT"' in template


def test_legacy_approval_actions_stack_full_width_on_mobile():
    template = text("app/templates/workflow/president_approvals.html")
    assert ".wf-decision-form{flex-direction:column;align-items:stretch}" in template
    assert ".wf-decision-form button{width:100%}" in template


def test_legacy_approval_route_and_auth_guard_unchanged():
    routes = text("app/workflow/routes.py")
    assert "@main_bp.route('/workflow/president-approvals')" in routes
    assert "def workflow_president_approvals():" in routes
    assert "if not (_can_view() or _can_decide()):" in routes
    assert "WORKFLOW_VIEW_ROLES = set(ADMIN_FAMILY_ROLES)" in routes
    assert "def workflow_president_decide" in routes
    for action in ["APPROVE", "RETURN", "REJECT"]:
        assert f'"{action}"' in routes or f"'{action}'" in routes


def test_legacy_approval_csrf_token_preserved():
    template = text("app/templates/workflow/president_approvals.html")
    assert "csrf_token()" in template


# --- 404/500 error pages: UTF-8 content, independent shell, no technical leak ---


def test_error_pages_do_not_extend_base_html():
    for rel in ["app/templates/errors/404.html", "app/templates/errors/500.html"]:
        content = text(rel)
        assert "{% extends" not in content, f"{rel} must stay independent of base.html"


def test_error_pages_have_viewport_meta():
    for rel in ["app/templates/errors/404.html", "app/templates/errors/500.html"]:
        content = text(rel)
        assert 'name="viewport"' in content
        assert "width=device-width" in content


def test_404_page_uses_correct_turkish_utf8_text():
    content = text("app/templates/errors/404.html")
    assert "Sayfa Bulunamadı" in content
    assert "Aradığınız sayfa bulunamadı veya taşınmış olabilir." in content
    assert "?" not in content.replace("width=device-width, initial-scale=1", "")


def test_500_page_uses_correct_turkish_utf8_text():
    content = text("app/templates/errors/500.html")
    assert "Beklenmeyen Hata" in content
    assert "İşlem sırasında geçici bir hata oluştu" in content
    assert "?" not in content.replace("width=device-width, initial-scale=1", "")


def test_error_pages_have_safe_return_link():
    for rel in ["app/templates/errors/404.html", "app/templates/errors/500.html"]:
        content = text(rel)
        assert "url_for('main.index')" in content
        assert "Ana Sayfaya Dön" in content


def test_error_pages_do_not_leak_technical_terms():
    for rel in ["app/templates/errors/404.html", "app/templates/errors/500.html"]:
        content = text(rel).lower()
        for term in FORBIDDEN_USER_FACING_TERMS:
            assert term not in content, f"{rel} leaks '{term}'"


def test_error_pages_meet_touch_target_and_reduced_motion():
    for rel in ["app/templates/errors/404.html", "app/templates/errors/500.html"]:
        content = text(rel)
        assert "min-height:44px" in content
        assert "prefers-reduced-motion: reduce" in content


def test_active_error_handler_passes_title_and_message_to_templates():
    handlers = text("app/error_handlers.py")
    assert 'render_template(\n            f"errors/{status_code}.html",' in handlers
    assert "title=title," in handlers
    assert "message=message," in handlers


# --- Settings.html: opt out of global auto-card conversion, keep controlled scroll ---


def test_settings_role_matrix_tables_opt_out_of_auto_card_conversion():
    settings = text("app/templates/settings.html")
    assert settings.count('data-no-mobile-card="1"') == 5
    assert 'class="role-default-table" data-no-mobile-card="1"' in settings
    assert 'class="matrix-table" data-no-mobile-card="1"' in settings


def test_android_mechanisms_honor_data_no_mobile_card_opt_out():
    for rel in [
        "app/static/js/bys360_android_responsive_completion_v1.js",
        "app/static/js/bys360_android_responsive_completion_v2.js",
    ]:
        js = text(rel)
        assert "[data-no-mobile-card='1']" in js


def test_faz4_controlled_scroll_css_unchanged_for_role_tables():
    css = text("app/static/css/faz4_support_account_mobile.css")
    compact = "".join(css.split())
    assert ".role-default-table,.matrix-table{display:block;overflow-x:auto;white-space:nowrap}" in compact


# --- survey_manage.html mobile bulk-selection fix ---


def test_faz4_js_restores_checkbox_in_mobile_card_view():
    js = text("app/static/js/faz4_support_account_mobile.js")
    assert "selectSource" in js
    assert "faz4-mobile-record-card__select" in js
    assert "selectSource.dispatchEvent(new Event('change', {bubbles:true}));" in js


def test_faz4_css_defines_select_control_with_touch_target():
    css = text("app/static/css/faz4_support_account_mobile.css")
    assert ".faz4-mobile-record-card__select{" in css
    assert "min-height:44px" in css


def test_survey_manage_checkbox_and_selection_js_unchanged():
    template = text("app/templates/survey_manage.html")
    assert 'class="survey-bulk-checkbox"' in template
    assert "faz4_support_account_mobile.js" in template


# --- notifications_list.html bulk-selection touch target ---


def test_notification_select_is_a_label_with_touch_target():
    template = text("app/templates/notifications_list.html")
    assert '<label class="notification-select">' in template
    assert "min-height:44px" in template
    assert "min-width:44px" in template


# --- Scope guards: nothing outside the intended Phase 11B footprint ---


def test_mobile_flutter_directory_is_untouched_by_this_phase():
    # Phase 11B never edits mobile_flutter/; this only asserts the directory,
    # if present, is not referenced from any file this phase modified.
    for rel in [
        "app/templates/workflow/president_approvals.html",
        "app/templates/settings.html",
        "app/templates/notifications_list.html",
        "app/static/js/faz4_support_account_mobile.js",
        "app/static/css/faz4_support_account_mobile.css",
        "app/templates/errors/404.html",
        "app/templates/errors/500.html",
    ]:
        assert "mobile_flutter" not in text(rel)


def test_pilot_template_titles_are_free_of_technical_jargon():
    error_404 = text("app/templates/errors/404.html").lower()
    error_500 = text("app/templates/errors/500.html").lower()
    for term in FORBIDDEN_USER_FACING_TERMS:
        assert term not in error_404
        assert term not in error_500
