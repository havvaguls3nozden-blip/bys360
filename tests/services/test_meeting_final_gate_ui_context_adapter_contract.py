"""BYS360 Meeting Final Gate -- UI context adapter contract (Dalga 2).

CONTEXT: prior to this wave, `app/templates/performance/meeting_development_
faz4.html` (the "final-gate" route) shared the exact same generic
"Hatirlatma ve Gelisim Takibi" body as the other meeting-family templates,
reading only `page_summary`/`reminder_items`/`overdue_items`/
`development_items`/`mail_items` -- none of which `build_final_gate_
context()` ever supplied. This wave rewrites ONLY the Final Gate template
body to render the real fields the context builder actually returns:
`status`, `errors`, `warnings`, `passed`, `final_checks` -- re-verified fresh
from current source (also confirming these ARE the genuine, still-accurate
contract, unlike the P0 wave's task description which named 4 fields that
did not exist). `final_checks` is a STATIC 6-item reference list (code/
title/expected/priority describing WHAT the gate checks, not a per-item
pass/fail result) -- deliberately rendered as a descriptive checklist,
separate from the DYNAMIC, computed `errors`/`warnings`/`passed` lists.

CRITICAL FINDING (disclosed, not fixed -- out of this wave's scope): a real,
isolated `build_final_gate_context()` call against the actual repo currently
returns `status="KONTROL GEREKİYOR"` with 9 real errors (missing tokens in
`app/templates/base.html` and `app/menu_registry.py` that `REQUIRED_TOKENS`
expects). This is a genuinely pre-existing, previously-invisible backend
finding -- the whole point of this wave is to surface it honestly, not to
silently "fix" it (fixing would mean editing `base.html`/`menu_registry.py`
content, explicitly out of scope: "Backend'in gerçekten üretmediği hiçbir
bilgiyi uydurma" cuts both ways -- neither fabricate passing data nor hide
real failing data). Tests below therefore assert against the REAL, current
9-error/0-warning/27-passed shape where useful, and against controlled
fixture data (via direct `render_template()` calls with an explicit context
dict) where a specific error/warning/empty scenario needs to be forced
without touching backend code.

Backend is completely untouched by this wave: `build_final_gate_context()`
and `meeting_development_faz4_routes.py` are byte-identical to the fixed
pre-wave ref. No new CSS -- the new body reuses only pre-existing `.bys-md-*`
classes already defined in `app/static/css/meeting_development_c_shared.css`
(untouched, byte-identical). The template's 2 pre-existing
`style="margin-top:16px;"` occurrences are preserved byte-for-byte (same
count, same string) -- the repo-wide style ledger (1035/64/225) is therefore
completely unaffected; no CSP-manifest wave entry was needed.

This file uses real, isolated Flask apps (module-scoped, UUID-based temp
SQLite, matching this repo's established fixture pattern) and real ORM
writes -- never string-interpolated SQL, never `|safe`.
"""
from __future__ import annotations

import html
import re
import subprocess
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_FILE = "app/templates/performance/meeting_development_faz4.html"
ROUTE_FILE = "app/performance/meeting_development_faz4_routes.py"
CONTEXT_BUILDER_FILE = "app/services/performance/meeting_development_final_gate.py"
P0_TEMPLATE_FILE = "app/templates/performance/meeting_p0_completion.html"

# Tip of phase5-critical-lint-clean-v1 immediately before this wave's own
# template rewrite -- the repo state where Final Gate still shared the
# generic meeting-family shell. Fixed, historical; never affected by any
# later commit.
PRE_WAVE_REF = "a6ec720a7507168a7744d36242df1a2468c2bce7"

OTHER_SIX_MEETING_TEMPLATES: tuple[str, ...] = (
    "app/templates/performance/meeting_development_faz3.html",
    "app/templates/performance/meeting_development_scenarios.html",
    "app/templates/performance/meeting_final_closure.html",
    "app/templates/performance/meeting_p1_scope.html",
    "app/templates/performance/meeting_p2_archive_notes.html",
    "app/templates/performance/meeting_rule_enforcement.html",
)
MEETING_FAMILY_SHARED_CSS = "app/static/css/meeting_development_c_shared.css"

_OLD_GENERIC_MARKERS = ("page_summary", "reminder_items", "overdue_items", "development_items", "mail_items")


def _normalize_line_endings(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def _git_show(ref: str, relative_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{ref}:{relative_path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, f"'git show {ref}:{relative_path}' failed: {result.stderr!r}"
    return result.stdout


# ---------------------------------------------------------------------------
# 1) The Final Gate template source now references the real context keys.
# ---------------------------------------------------------------------------


def test_final_gate_template_source_references_real_context_keys() -> None:
    text = (REPO_ROOT / TEMPLATE_FILE).read_text(encoding="utf-8")
    for key in ("status", "errors", "warnings", "passed", "final_checks"):
        assert key in text, f"Expected real context key '{key}' to be referenced in the Final Gate template."


# 2) Old generic shell no longer used.
def test_final_gate_template_no_longer_uses_the_old_generic_shell_variables() -> None:
    text = (REPO_ROOT / TEMPLATE_FILE).read_text(encoding="utf-8")
    for marker in _OLD_GENERIC_MARKERS:
        assert marker not in text, f"Final Gate template still references old generic shell variable '{marker}'."


# ---------------------------------------------------------------------------
# Jinja/CSS safety static checks.
# ---------------------------------------------------------------------------


def test_final_gate_template_has_no_new_style_beyond_the_two_preexisting() -> None:
    text = (REPO_ROOT / TEMPLATE_FILE).read_text(encoding="utf-8")
    assert "<style" not in text.lower(), "Final Gate template must not add a <style> block."
    style_attr_count = len(re.findall(r'\sstyle\s*=\s*"', text))
    assert style_attr_count == 2, (
        f"Expected exactly the 2 pre-existing style=\"margin-top:16px;\" attributes, found {style_attr_count}."
    )
    assert text.count('class="bys-md-card" style="margin-top:16px;"') == 2


# 13/14/15) no |safe, no inline handler, no javascript: URL.
def test_final_gate_template_has_no_jinja_safety_violations() -> None:
    text = (REPO_ROOT / TEMPLATE_FILE).read_text(encoding="utf-8")
    assert "|safe" not in text, "Final Gate template must not use the |safe filter."
    assert not re.search(r'\bon\w+\s*=\s*"', text, re.IGNORECASE), "Final Gate template must not add an inline event handler."
    assert "javascript:" not in text.lower(), "Final Gate template must not add a javascript: URL."


def test_final_gate_template_has_no_script_block_or_dangerous_js_sinks() -> None:
    """This template has zero interactivity (pure read-only status report) --
    stronger than the old shared shell's single reload-button listener.
    Direct replacement for test_csp_wave3_meeting_group_a_contract.py's own
    (now-removed-for-this-path) test_meeting_group_a_reload_button_uses_id_
    and_click_listener."""
    text = (REPO_ROOT / TEMPLATE_FILE).read_text(encoding="utf-8")
    assert "<script" not in text.lower()
    assert "addEventListener" not in text
    assert "data-onclick" not in text
    for forbidden in ("eval(", "new Function(", "document.write("):
        assert forbidden not in text, f"Final Gate template contains a forbidden JS sink: {forbidden}"


def test_final_gate_rendered_output_has_no_script_or_inline_handlers(final_gate_response_body) -> None:
    """Real-render counterpart (not just static source read) to the check
    above -- direct replacement for test_csp_wave3_meeting_group_a_
    contract.py's own (now-removed-for-this-path)
    test_meeting_group_a_render_includes_reload_button_script_hook (which
    asserted the OPPOSITE: that a reload-button script hook DID render).
    Scoped to the Final Gate shell content only, not the whole page, since
    base.html legitimately carries its own <script> blocks (topbar/sidebar/
    assistant JS) that are out of this wave's scope."""
    _status, body = final_gate_response_body
    start = body.find('data-page="meeting-final-gate"')
    assert start != -1, "Could not locate the Final Gate shell content in the rendered response."
    end = body.find("</div>\n</div>", start)
    shell_only = body[start : end if end != -1 else start + 20000]
    assert "<script" not in shell_only.lower()
    assert "addEventListener" not in shell_only
    assert not re.search(r'\bon\w+\s*=\s*"', shell_only, re.IGNORECASE)
    assert "javascript:" not in shell_only.lower()
    assert "data-onclick" not in shell_only
    for forbidden in ("eval(", "new Function(", "document.write("):
        assert forbidden not in shell_only


def test_final_gate_template_links_shared_css_exactly_once_and_no_new_css_file() -> None:
    text = (REPO_ROOT / TEMPLATE_FILE).read_text(encoding="utf-8")
    matches = re.findall(
        r"""<link\s+rel=["']stylesheet["']\s+href=["']\{\{\s*url_for\(\s*["']static["']\s*,\s*"""
        r"""filename=["']css/meeting_development_c_shared\.css["']\s*\)\s*\}\}["']\s*/?>""",
        text,
    )
    assert len(matches) == 1, f"Expected exactly one shared-CSS <link>, found {len(matches)}."


def test_no_new_css_file_was_added() -> None:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--porcelain=v1", "--untracked-files=all", "--", "app/static/css/"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "", f"Unexpected new/changed file(s) under app/static/css/: {result.stdout}"


def test_shared_meeting_css_file_is_untouched() -> None:
    current = _normalize_line_endings((REPO_ROOT / MEETING_FAMILY_SHARED_CSS).read_bytes())
    pre_wave = _normalize_line_endings(_git_show(PRE_WAVE_REF, MEETING_FAMILY_SHARED_CSS))
    assert current == pre_wave, f"{MEETING_FAMILY_SHARED_CSS}: byte content changed -- must be untouched."


# ---------------------------------------------------------------------------
# 6) Backend untouched: route file and context builder byte-identical to
#    the fixed pre-wave ref.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", [ROUTE_FILE, CONTEXT_BUILDER_FILE])
def test_final_gate_backend_files_are_untouched_by_this_wave(relative_path: str) -> None:
    current = _normalize_line_endings((REPO_ROOT / relative_path).read_bytes())
    pre_wave = _normalize_line_endings(_git_show(PRE_WAVE_REF, relative_path))
    assert current == pre_wave, f"{relative_path}: byte content changed since pre-wave ref -- backend must be untouched."


# 22) P0 template byte-identical (untouched by this wave).
def test_p0_template_is_untouched_by_this_wave() -> None:
    current = _normalize_line_endings((REPO_ROOT / P0_TEMPLATE_FILE).read_bytes())
    pre_wave = _normalize_line_endings(_git_show(PRE_WAVE_REF, P0_TEMPLATE_FILE))
    assert current == pre_wave, f"{P0_TEMPLATE_FILE}: byte content changed -- must be untouched by this wave."


# 23) Other 6 meeting templates untouched.
@pytest.mark.parametrize("relative_path", OTHER_SIX_MEETING_TEMPLATES)
def test_other_six_meeting_templates_are_untouched(relative_path: str) -> None:
    current = _normalize_line_endings((REPO_ROOT / relative_path).read_bytes())
    pre_wave = _normalize_line_endings(_git_show(PRE_WAVE_REF, relative_path))
    assert current == pre_wave, f"{relative_path}: byte content changed -- other 6 meeting templates must be untouched."


# ---------------------------------------------------------------------------
# Real, isolated, authenticated Flask app -- exercises the REAL route/
# context builder against the real repo (no mocking of build_final_gate_
# context() itself), which currently surfaces 9 real errors (see module
# docstring's "CRITICAL FINDING").
# ---------------------------------------------------------------------------

_TEST_DB_ROOT = Path("C:/bys360/audit_tmp/final_gate_ui_contract/test_dbs")
_SAFE_RENDER_FALLBACK_MARKERS = ("\u015fablonunda hata var", "\u015fablonu hatal\u0131")


@pytest.fixture(scope="module")
def final_gate_env():
    mp = pytest.MonkeyPatch()
    _TEST_DB_ROOT.mkdir(parents=True, exist_ok=True)
    db_path = _TEST_DB_ROOT / f"{uuid.uuid4().hex}.sqlite3"

    mp.setenv("APP_ENV", "testing")
    mp.setenv("FLASK_ENV", "testing")
    mp.setenv("SECRET_KEY", "test-secret-key-for-final-gate-ui-contract-min-length-ok")
    mp.setenv("DEFAULT_FIRST_LOGIN_PASSWORD", "test-password")
    mp.setenv("FLASK_SKIP_SCHEMA_VALIDATION", "1")
    mp.setenv("AUTO_REPAIR_SCHEMA", "false")
    mp.setenv("STRICT_SCHEMA_CHECK", "false")
    mp.setenv("REQUIRE_DOTENV_FILE", "false")
    mp.setenv("STRICT_ENV_VALIDATION", "false")
    mp.setenv("WTF_CSRF_ENABLED", "false")
    mp.setenv("DATABASE_URL", "sqlite:///" + db_path.as_posix())
    mp.setenv("MAIL_SUPPRESS_SEND", "true")
    mp.setenv("SCHEDULER_ENABLED", "false")

    from app import create_app
    from config import Config

    mp.setattr(Config, "APP_ENV", "testing")
    mp.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite:///" + db_path.as_posix())
    mp.setattr(Config, "SQLALCHEMY_ENGINE_OPTIONS", {})

    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI="sqlite:///" + db_path.as_posix(),
    )

    from app.extensions import db
    from app.models import User

    with app.app_context():
        db.create_all()
        user = User(
            sicil_no="fgcontract1",
            email="fgcontract@ktb.gov.tr",
            ad="FinalGate",
            soyad="Kontrat",
            role="admin",
            is_active=True,
            must_change_password=False,
            must_set_security_question=False,
        )
        user.set_password("FinalGateContractTestKey1!")
        db.session.add(user)
        db.session.commit()

    client = app.test_client()
    login_response = client.post(
        "/login",
        data={"sicil_or_email": "fgcontract1", "password": "FinalGateContractTestKey1!"},
        follow_redirects=False,
    )
    assert login_response.status_code == 302, f"Test admin login failed: status={login_response.status_code}"
    assert "/login" not in (login_response.headers.get("Location") or ""), (
        "Still redirected to /login after POST -- authentication may have failed."
    )

    yield app, client

    mp.undo()


@pytest.fixture(scope="module")
def final_gate_response_body(final_gate_env):
    _app, client = final_gate_env
    response = client.get("/performance/meeting-development/final-gate", follow_redirects=True)
    return response.status_code, response.get_data(as_text=True)


@pytest.fixture(scope="module")
def real_final_gate_context(final_gate_env):
    """The REAL, unmocked build_final_gate_context() output against the
    actual repo -- proves this wave's fixture-independent claims (9 real
    errors, 0 warnings, 27 passed, 6 final_checks) without hand-seeding any
    data, and gives the rendered-HTML tests below ground truth to assert
    against."""
    app, _client = final_gate_env
    with app.app_context():
        from app.services.performance.meeting_development_final_gate import build_final_gate_context

        return build_final_gate_context()


# 16) Authenticated GET 200.
def test_final_gate_route_returns_200(final_gate_response_body) -> None:
    status, body = final_gate_response_body
    assert status == 200
    for marker in _SAFE_RENDER_FALLBACK_MARKERS:
        assert marker not in body, "Response looks like a safe_render() fallback stub."


# 18) H1/title Final Gate-specific.
def test_final_gate_title_and_h1_are_final_gate_specific(final_gate_response_body) -> None:
    _status, body = final_gate_response_body
    assert "Final Kontrol" in body
    h1_match = re.search(r'<h1[^>]*class="bys-md-title"[^>]*>([^<]*)</h1>', body)
    assert h1_match, "Expected a <h1 class='bys-md-title'> in the response."
    assert h1_match.group(1).strip() == "Final Kontrol"
    assert h1_match.group(1).strip() != "Hatırlatma ve Gelişim Takibi"


# 3) status renders.
def test_status_is_rendered(final_gate_response_body, real_final_gate_context) -> None:
    _status, body = final_gate_response_body
    assert f"Genel durum: {real_final_gate_context['status']}" in body


# 4) passed renders.
def test_passed_is_rendered(final_gate_response_body, real_final_gate_context) -> None:
    _status, body = final_gate_response_body
    assert f"{len(real_final_gate_context['passed'])} doğrulandı" in body
    # spot-check a handful of the real passed entries appear verbatim
    for entry in real_final_gate_context["passed"][:5]:
        assert entry in body, f"Expected real passed entry in response body: {entry!r}"


# 5) final_checks renders.
def test_final_checks_are_rendered(final_gate_response_body, real_final_gate_context) -> None:
    _status, body = final_gate_response_body
    for item in real_final_gate_context["final_checks"]:
        assert item["title"] in body, f"Expected final_checks title in response body: {item['title']!r}"
        assert item["expected"] in body, f"Expected final_checks description in response body: {item['expected']!r}"


# 6) errors populated scenario (real, current repo state has 9).
def test_errors_populated_scenario_is_rendered(final_gate_response_body, real_final_gate_context) -> None:
    _status, body = final_gate_response_body
    assert real_final_gate_context["errors"], (
        "This test asserts the currently-real populated-errors scenario; if the underlying "
        "backend finding is ever fixed, this assertion will correctly need updating to the "
        "empty-scenario test's shape instead."
    )
    for entry in real_final_gate_context["errors"]:
        # Jinja autoescape correctly turns a literal '>' in these messages
        # (e.g. "... -> ...") into '&gt;' -- compare against the same
        # escaped form html.escape() produces, proving escaping is genuinely
        # active rather than bypassed with |safe.
        assert html.escape(entry) in body, f"Expected real (HTML-escaped) error entry in response body: {entry!r}"
    assert f"{len(real_final_gate_context['errors'])} hata" in body


# 7) errors empty scenario -- direct render_template() with a controlled,
#    explicit context (no backend mocking, just a different template-only
#    input) to prove the empty-state path independently of the real repo's
#    current (populated) error state.
def test_errors_empty_scenario_renders_safely(final_gate_env) -> None:
    app, _client = final_gate_env
    with app.test_request_context("/"):
        from flask import render_template

        html = render_template(
            "performance/meeting_development_faz4.html",
            status="GEÇTİ",
            errors=[],
            warnings=[],
            passed=["Örnek doğrulama"],
            final_checks=[{"code": "X1", "title": "Örnek", "expected": "Örnek beklenti", "priority": "P0"}],
        )
    assert "Açık hata bulunmuyor." in html
    assert "0 hata" in html


# 8) warnings populated scenario.
def test_warnings_populated_scenario_renders(final_gate_env) -> None:
    app, _client = final_gate_env
    with app.test_request_context("/"):
        from flask import render_template

        html = render_template(
            "performance/meeting_development_faz4.html",
            status="GEÇTİ",
            errors=[],
            warnings=["Ayar veritabanında görünmedi: örnek_ayar_anahtarı"],
            passed=[],
            final_checks=[],
        )
    assert "Ayar veritabanında görünmedi: örnek_ayar_anahtarı" in html
    assert "1 uyarı" in html


# 9) warnings empty scenario (real, current repo state has 0).
def test_warnings_empty_scenario_renders_safely(final_gate_response_body, real_final_gate_context) -> None:
    _status, body = final_gate_response_body
    assert real_final_gate_context["warnings"] == [], (
        "This test asserts the currently-real empty-warnings scenario."
    )
    assert "Uyarı bulunmuyor." in body
    assert "0 uyarı" in body


# 10) success/failure states are visually distinguished.
def test_success_and_failure_states_are_visually_distinguished(final_gate_env) -> None:
    app, _client = final_gate_env
    with app.test_request_context("/"):
        from flask import render_template

        passing_html = render_template(
            "performance/meeting_development_faz4.html",
            status="GEÇTİ",
            errors=[],
            warnings=[],
            passed=[],
            final_checks=[],
        )
        failing_html = render_template(
            "performance/meeting_development_faz4.html",
            status="KONTROL GEREKİYOR",
            errors=["Örnek hata"],
            warnings=[],
            passed=[],
            final_checks=[],
        )
    assert "bys-md-badge-success" in passing_html
    assert "Genel durum: GEÇTİ" in passing_html
    assert "bys-md-badge-danger" in failing_html
    assert "Genel durum: KONTROL GEREKİYOR" in failing_html


# 11) None/0/False handled correctly (no literal "None"; zero counts render
#     as "0", not as "no data").
def test_none_and_zero_render_correctly(final_gate_env) -> None:
    app, _client = final_gate_env
    with app.test_request_context("/"):
        from flask import render_template

        html = render_template(
            "performance/meeting_development_faz4.html",
            status="GEÇTİ",
            errors=[],
            warnings=[],
            passed=[],
            final_checks=[],
        )
    assert re.search(r">\s*None\s*<", html) is None, "Literal 'None' must never appear as rendered text."
    assert "0 hata" in html
    assert "0 uyarı" in html
    assert "0 doğrulandı" in html


# 12) No raw dict/JSON leakage.
def test_no_raw_dict_or_json_leaks_into_response(final_gate_response_body) -> None:
    _status, body = final_gate_response_body
    assert "{'status'" not in body and '{"status"' not in body
    assert "{'code'" not in body and '{"code"' not in body


# 17) Fixture context values genuinely present in response body (via real,
#     unmocked context -- see real_final_gate_context fixture).
def test_real_context_values_are_genuinely_in_response_body(final_gate_response_body, real_final_gate_context) -> None:
    _status, body = final_gate_response_body
    assert real_final_gate_context["final_checks"][0]["title"] in body
    assert str(len(real_final_gate_context["final_checks"])) in body


# 10-real-http) old generic body is no longer this route's main content.
def test_final_gate_old_generic_shell_heading_is_not_the_main_content(final_gate_response_body) -> None:
    _status, body = final_gate_response_body
    h1_match = re.search(r'<h1[^>]*class="bys-md-title"[^>]*>([^<]*)</h1>', body)
    assert h1_match
    assert h1_match.group(1).strip() != "Hatırlatma ve Gelişim Takibi"


# ---------------------------------------------------------------------------
# 19) url_map unchanged.
# ---------------------------------------------------------------------------

EXPECTED_URL_MAP_TOTAL = 985


def test_url_map_route_count_is_unchanged(final_gate_env) -> None:
    app, _client = final_gate_env
    total = len(list(app.url_map.iter_rules()))
    assert total == EXPECTED_URL_MAP_TOTAL, f"url_map route count is {total}; expected {EXPECTED_URL_MAP_TOTAL}."


# ---------------------------------------------------------------------------
# 20) Style inventory does not worsen; handler/javascript stay 0/0.
# ---------------------------------------------------------------------------

EXPECTED_ACTIVE_STYLE_TOTAL = 1035
EXPECTED_DYNAMIC_STYLE_TOTAL = 64
EXPECTED_STYLE_BLOCK_TOTAL = 225


def test_repo_wide_style_and_handler_inventory_is_unchanged() -> None:
    from tests.security._bys360_style_inventory import compute_inventory_from_worktree

    inventory = compute_inventory_from_worktree()
    assert inventory.active_static_total == EXPECTED_ACTIVE_STYLE_TOTAL, (
        f"active_static_total is {inventory.active_static_total}; expected {EXPECTED_ACTIVE_STYLE_TOTAL} (unchanged)."
    )
    assert inventory.dynamic_total == EXPECTED_DYNAMIC_STYLE_TOTAL
    assert inventory.style_block_total == EXPECTED_STYLE_BLOCK_TOTAL, (
        f"style_block_total is {inventory.style_block_total}; expected {EXPECTED_STYLE_BLOCK_TOTAL} (must not worsen)."
    )
    assert inventory.inline_handler_total == 0
    assert inventory.javascript_url_total == 0


# ---------------------------------------------------------------------------
# 21) CSP header/nonce unchanged.
# ---------------------------------------------------------------------------

STYLE_DIRECTIVES = ["style-src", "style-src-elem", "style-src-attr"]
EXPECTED_STYLE_DIRECTIVE_VALUES = {
    "style-src": "'self' 'unsafe-inline' https:",
    "style-src-elem": "'self' 'unsafe-inline' https:",
    "style-src-attr": "'unsafe-inline'",
}


def _csp_header_value(response) -> str:
    value = response.headers.get("Content-Security-Policy")
    if value is None:
        value = response.headers.get("Content-Security-Policy-Report-Only")
    assert value, "No CSP header found in the response."
    return value


def _parse_csp_directives(policy_text: str) -> dict[str, str]:
    directives: dict[str, str] = {}
    for chunk in policy_text.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split(None, 1)
        directives[parts[0]] = parts[1] if len(parts) > 1 else ""
    return directives


def test_csp_style_directives_are_byte_identical_to_style1_end_state(client) -> None:
    response = client.get("/login")
    directives = _parse_csp_directives(_csp_header_value(response))
    for directive, expected_value in EXPECTED_STYLE_DIRECTIVE_VALUES.items():
        assert directive in directives
        assert directives[directive] == expected_value


@pytest.mark.parametrize("directive", STYLE_DIRECTIVES)
def test_csp_style_directives_contain_no_nonce_token(client, directive: str) -> None:
    response = client.get("/login")
    directives = _parse_csp_directives(_csp_header_value(response))
    assert "'nonce-" not in directives.get(directive, "")


# ---------------------------------------------------------------------------
# 24) No new xfail introduced by this file.
# ---------------------------------------------------------------------------

_XFAIL_CALL_RE = re.compile(r"pytest" + r"\.xfail\(")
_XFAIL_MARK_RE = re.compile(r"@pytest" + r"\.mark\.xfail")


def test_this_file_introduces_no_xfail_usage() -> None:
    own_text = Path(__file__).read_text(encoding="utf-8")
    call_count = len(_XFAIL_CALL_RE.findall(own_text))
    mark_count = len(_XFAIL_MARK_RE.findall(own_text))
    assert call_count + mark_count == 0


# ---------------------------------------------------------------------------
# This file never writes to any application/template/CSS source path.
# ---------------------------------------------------------------------------


def test_this_file_never_writes_to_application_or_template_or_css_source_paths() -> None:
    forbidden_write_markers = (
        "write_text(",
        "write_bytes(",
        "shutil.copy",
        "shutil.move",
        "shutil.rmtree",
        "os.rename(",
        "os.remove(",
        "os.unlink(",
    )
    own_text = Path(__file__).read_text(encoding="utf-8")
    marker_def_start = own_text.index("forbidden_write_markers = (")
    marker_def_end = own_text.index(")\n", marker_def_start) + 1
    scan_text = own_text[:marker_def_start] + own_text[marker_def_end:]
    hits = [marker for marker in forbidden_write_markers if marker in scan_text]
    assert hits == []
