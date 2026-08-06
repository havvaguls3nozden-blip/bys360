"""Phase 11C remaining critical responsive screens - static contract gate.

Statik metin tabanlı kontrat testleri: gerçek tarayıcı/cihaz render'ı
doğrulamaz, yalnızca kaynak koddaki responsive/güvenlik/dil kurallarının
var olduğunu ve gerilemediğini denetler. Phase 11A/11B'deki
test_phase11a/11b_*_contract.py dosyalarıyla aynı desen.

BYS360 Workflow Orphan Presentation Subsystem Temizliği update:
`test_president_approvals_route_template_contract_unchanged` below used to
also `.read_text()` `app/workflow/routes.py` to assert its (never actually
live -- see `tests/quality/test_workflow_orphan_presentation_subsystem_
cleanup_contract.py` for the full evidence) route/view-name pair was
"unchanged". That file was deleted along with the rest of its confirmed-
dead subsystem; those two assertions were removed, leaving only the
still-meaningful "canonical, genuinely active president-approvals route
file still exposes both its URL aliases" checks.
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


# --- survey_results.html: share modal now has base positioning CSS (P0 fix) ---


def test_survey_results_share_modal_has_positioning_css():
    template = text("app/templates/survey_results.html")
    assert ".share-modal{position:fixed;inset:0;display:flex;" in template
    assert ".share-modal[hidden]{display:none}" in template
    assert ".share-dialog{width:min(560px,100%)" in template


def test_survey_results_share_dialog_fits_mobile_viewport_height():
    template = text("app/templates/survey_results.html")
    assert "max-height:calc(100dvh - 48px)" in template
    assert "overflow-y:auto" in template


def test_survey_results_share_modal_markup_matches_css_classes():
    template = text("app/templates/survey_results.html")
    assert 'class="share-modal" id="surveyShareModal" hidden' in template
    assert 'class="share-dialog"' in template
    assert 'class="share-dialog-head"' in template


# --- settings.html: 6th assistant-matrix table now opts out of auto-card conversion ---


def test_settings_assistant_role_matrix_opts_out_of_auto_card_conversion():
    settings = text("app/templates/settings.html")
    assert settings.count('data-no-mobile-card="1"') == 6
    assert 'style="min-width:980px;margin:0;" data-no-mobile-card="1"' in settings


# --- org_units_list.html: AI panel grids now collapse on mobile ---


def test_org_units_ai_panel_grids_collapse_on_mobile():
    template = text("app/templates/org_units_list.html")
    compact = "".join(template.split())
    assert ".ai-action-grid,.ai-heat-grid{grid-template-columns:1fr}" in compact


def test_org_units_ai_grid_fix_is_inside_existing_breakpoint_not_a_new_one():
    template = text("app/templates/org_units_list.html")
    idx = template.find("@media (max-width:700px)")
    next_media = template.find("@media", idx + 1)
    block = template[idx : next_media if next_media != -1 else idx + 400]
    assert ".ai-action-grid,.ai-heat-grid{grid-template-columns:1fr}" in "".join(block.split())


# --- login.html: standalone screen now gets its own foundation-equivalent coverage ---


def test_login_viewport_meta_includes_safe_area_cover():
    login = text("app/templates/login.html")
    assert 'content="width=device-width, initial-scale=1, viewport-fit=cover"' in login


def test_login_loader_animations_respect_reduced_motion():
    login = text("app/templates/login.html")
    assert "@media (prefers-reduced-motion: reduce){" in login
    assert ".page-loader-ring" in login
    assert ".page-loader-logo" in login


def test_login_has_dedicated_focus_visible_rule():
    login = text("app/templates/login.html")
    assert ".form-input:focus-visible" in login
    assert ".btn-login:focus-visible" in login


def test_login_input_font_size_is_explicit_not_inherited():
    login = text("app/templates/login.html")
    idx = login.index(".form-input{")
    block_end = login.index("}", idx)
    assert "font-size:16px" in login[idx:block_end]


def test_login_does_not_extend_base_html_by_design():
    # login.html is intentionally standalone (pre-authentication shell); this
    # guards against someone assuming it inherits the foundation CSS via
    # base.html when it in fact needs its own equivalent rules (as added above).
    login = text("app/templates/login.html")
    assert "{% extends" not in login


# --- Scope guards: nothing outside the intended Phase 11C footprint ---


def test_president_approvals_route_template_contract_unchanged():
    canonical_routes = text(
        "app/performance/process_engine_phase6_president_approvals_routes.py"
    )
    assert "/performance/president-approvals" in canonical_routes
    assert "/performans/baskan-onaylari" in canonical_routes


def test_error_handlers_core_module_untouched_by_this_phase():
    # app/core/error_handlers.py is dead code (Phase 11B finding) but cleanup
    # of it is explicitly out of scope for Phase 11C; this only asserts the
    # active handler (app/error_handlers.py) still wires errors/{code}.html.
    active_handlers = text("app/error_handlers.py")
    assert 'render_template(\n            f"errors/{status_code}.html",' in active_handlers


def test_mobile_flutter_directory_is_untouched_by_this_phase():
    for rel in [
        "app/templates/survey_results.html",
        "app/templates/settings.html",
        "app/templates/org_units_list.html",
        "app/templates/login.html",
    ]:
        assert "mobile_flutter" not in text(rel)


def test_pilot_templates_are_free_of_technical_jargon():
    for rel in [
        "app/templates/survey_results.html",
        "app/templates/settings.html",
        "app/templates/org_units_list.html",
        "app/templates/login.html",
    ]:
        content = text(rel).lower()
        for term in FORBIDDEN_USER_FACING_TERMS:
            assert term not in content, f"{rel} leaks '{term}'"


def test_no_new_global_mobile_patch_css_file_created():
    # Phase 11C's mandate is to extend existing files, not create a 4th/5th/6th
    # global mobile CSS layer. Guard against a stray new file matching that
    # naming convention landing in this commit's likely footprint.
    forbidden_names = [
        "mobile_hotfix",
        "mobile_final_fix",
        "responsive_patch_v2",
    ]
    css_dir = ROOT / "app" / "static" / "css"
    existing = {p.name for p in css_dir.glob("*.css")}
    for forbidden in forbidden_names:
        assert not any(forbidden in name for name in existing)
