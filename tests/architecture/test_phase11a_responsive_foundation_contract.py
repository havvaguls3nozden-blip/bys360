"""Phase 11A responsive web foundation - static contract gate.

Statik metin tabanlı kontrat testleri: gerçek tarayıcı/cihaz render'ı
doğrulamaz (bu depoda Playwright/Selenium kurulu değildir, bilinçli olarak
kurulmamıştır), yalnızca kaynak koddaki responsive/PWA/erişilebilirlik
kurallarının var olduğunu ve gerilemediğini denetler.
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


def _block(content: str, block_name: str) -> str:
    start_tag = "{% block " + block_name + " %}"
    end_tag = "{% endblock %}"
    start = content.index(start_tag) + len(start_tag)
    end = content.index(end_tag, start)
    return content[start:end]


def test_base_template_has_single_viewport_meta_with_cover():
    base = text("app/templates/base.html")
    assert base.count('name="viewport"') == 1
    assert 'content="width=device-width, initial-scale=1, viewport-fit=cover"' in base


def test_base_template_has_single_manifest_link():
    base = text("app/templates/base.html")
    assert base.count("rel=\"manifest\"") == 1


def test_base_template_status_bar_style_is_consistent():
    base = text("app/templates/base.html")
    marker = 'name="apple-mobile-web-app-status-bar-style" content="'
    values = set()
    idx = 0
    while True:
        idx = base.find(marker, idx)
        if idx == -1:
            break
        start = idx + len(marker)
        end = base.index('"', start)
        values.add(base[start:end])
        idx = end
    assert values == {"black-translucent"}


def test_base_template_loads_responsive_foundation_css_last_in_head():
    base = text("app/templates/base.html")
    head, _, _rest = base.partition("</head>")
    assert "bys360_responsive_foundation_v11a.css" in head
    assert head.rindex("bys360_responsive_foundation_v11a.css") > head.rindex(
        "bys360_assistant_no_chat_intro_open_fix_v34.css"
    )


def test_mobile_drawer_escape_closes_and_returns_focus():
    base = text("app/templates/base.html")
    assert "e.key==='Escape' && sidebar.classList.contains('mobile-open')" in base
    assert "setMobile(false);toggle.focus();" in base


def test_mobile_overlay_click_also_returns_focus():
    base = text("app/templates/base.html")
    assert "overlay.addEventListener('click',function(){setMobile(false);toggle.focus();});" in base


def test_menu_toggle_has_aria_expanded_state():
    base = text("app/templates/base.html")
    assert 'aria-expanded="false"' in base
    assert "toggle.setAttribute('aria-expanded'" in base


def test_responsive_foundation_css_defines_touch_targets_and_safe_area():
    css = text("app/static/css/bys360_responsive_foundation_v11a.css")
    assert "--bys-safe-top" in css
    assert "--bys-safe-bottom" in css
    assert "--bys-touch-min: 44px" in css
    assert ".mini-btn" in css
    assert ".menu-toggle" in css
    assert "min-height: var(--bys-touch-min) !important" in css


def test_responsive_foundation_css_guards_reduced_motion():
    css = text("app/static/css/bys360_responsive_foundation_v11a.css")
    assert "prefers-reduced-motion: reduce" in css
    assert ".page-loader-ring" in css


def test_responsive_foundation_css_defines_focus_visible_baseline():
    css = text("app/static/css/bys360_responsive_foundation_v11a.css")
    assert ":focus-visible" in css


def test_responsive_foundation_css_scopes_safe_area_padding_to_standalone_pwa():
    css = text("app/static/css/bys360_responsive_foundation_v11a.css")
    assert "display-mode: standalone" in css
    assert ".topbar" in css


def test_president_approvals_action_buttons_meet_touch_target():
    template = text(
        "app/templates/performance/process_engine_president_approvals.html"
    )
    assert ".pa-btn{border:0;border-radius:999px;padding:10px 14px;min-height:44px" in template


def test_president_approvals_actions_stack_full_width_on_mobile():
    template = text(
        "app/templates/performance/process_engine_president_approvals.html"
    )
    assert ".pa-action-row{flex-direction:column;align-items:stretch}" in template
    assert ".pa-action-row .pa-btn{width:100%}" in template


def test_evaluation_form_criteria_row_collapses_to_single_column_on_mobile():
    styles = text(
        "app/templates/partials/evaluation_form/_evaluation_form_styles.html"
    )
    idx = styles.index("@media (max-width:760px)")
    next_media = styles.find("@media", idx + 1)
    block = styles[idx : next_media if next_media != -1 else len(styles)]
    compact = "".join(block.split())
    assert ".criteria-row{grid-template-columns:1fr" in compact


def test_pilot_template_titles_are_free_of_technical_jargon():
    pilot_templates = {
        "app/templates/base.html": ["title"],
        "app/templates/login.html": [],
        "app/templates/dashboard.html": ["title", "page_title"],
        "app/templates/admin_users.html": ["title", "page_title"],
        "app/templates/evaluation_form.html": ["title", "page_title"],
        "app/templates/performance/process_engine_president_approvals.html": [
            "title",
            "page_title",
        ],
    }
    for rel_path, block_names in pilot_templates.items():
        content = text(rel_path)
        for block_name in block_names:
            block_text = _block(content, block_name).lower()
            for term in FORBIDDEN_USER_FACING_TERMS:
                assert term not in block_text, f"{rel_path}:{block_name} leaks '{term}'"


def test_login_title_is_free_of_technical_jargon():
    login = text("app/templates/login.html").lower()
    start = login.index("<title>")
    end = login.index("</title>")
    title_text = login[start:end]
    for term in FORBIDDEN_USER_FACING_TERMS:
        assert term not in title_text
