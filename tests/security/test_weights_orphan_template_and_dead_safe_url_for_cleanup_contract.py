"""BYS360 Orphan Template + Dead Helper Micro-Cleanup -- cleanup contract.

CONTEXT: a dedicated 1-coordinator + 3-agent read-only investigation (each
agent independently searching the repo, then cross-checked by the
coordinator, including a live runtime identity probe -- never trusted on a
single agent's word alone) confirmed two dead-code candidates:

CANDIDATE A -- app/templates/weights.html (ORPHAN_CONFIRMED):
    No route anywhere calls ``render_template("weights.html", ...)`` /
    ``safe_render(...)``, no ``{% include/extends/import/from %}`` references
    it, no menu/nav registry entry, no dynamic/pattern-based template loader
    touches it, and a live, isolated ``create_app()`` + ``url_map``
    introspection shows none of the 4 endpoints it references
    (``main.performance_weight_create/edit/toggle_active/delete``) are
    registered anywhere. This was independently reached THREE separate ways:
    this wave's own Agent 1 (full-repo consumer scan + live url_map probe),
    the pre-existing ``tests/services/test_meeting_stale_navigation_endpoint_
    fix_contract.py`` (written by an earlier, unrelated wave that explicitly
    declared it NO_SUCCESSOR/orphan and out of scope), and the pre-existing
    ``tests/security/test_csp_wave6_criteria_weights_contract.py`` (whose own
    docstring already noted the same finding while working on an unrelated
    CSP fix). The nearest live route touching the same underlying
    ``PerformanceWeightConfig`` data, ``main.performance_hierarchy_settings``,
    is architecturally a single-record per-period upsert form, not the
    per-row list+CRUD ``weights.html`` expects -- explicitly NOT treated as a
    successor, and left completely untouched by this wave.

    ``app/templates/weight_create.html`` and ``app/templates/weight_edit.html``
    are the same orphan family (same zero-consumer profile) but were
    DELIBERATELY left out of this wave's scope (flagged as follow-up tech
    debt, not a broad cleanup) -- both are asserted below as untouched,
    still-present, byte-identical files.

CANDIDATE B -- app/template_safety.py::safe_url_for (DEAD_SHADOWED_HELPER):
    Registered only as a Jinja *environment global*
    (``app.jinja_env.globals.setdefault("safe_url_for", safe_url_for)``).
    Every real template render is unconditionally shadowed by
    ``app.route_support.safe_url_for``, injected into the per-render Jinja
    *context* by the app-wide context processor ``inject_route_helpers``
    (``app/routes.py`` -> ``app/services/ui_context/helpers.py``). Jinja's
    ``new_context()`` always merges per-render context vars on top of
    environment globals for the same key, so the context-processor version
    always wins -- confirmed both by reading Jinja2/Flask source and by a
    live runtime probe (render a template that prints
    ``{{ safe_url_for.__module__ }}.{{ safe_url_for.__qualname__ }}`` against
    a real, isolated ``create_app()``; result:
    ``app.route_support.safe_url_for``, reproduced independently by this
    wave's coordinator, not just an agent's claim). Zero direct Python
    callers of ``template_safety.safe_url_for`` were found anywhere
    (production or test) -- only ``route_support.safe_url_for`` has real
    consumers (~100+ importing files). The dead function (with its docstring)
    and its single Jinja-globals registration line were removed;
    ``register_template_safety()``'s other filters/globals (``or_dash``,
    ``safe_len``, the ``ai_*_label`` filters, ``about_modal_context``, the
    ``ChainableUndefined``/``finalize`` Jinja config) and
    ``route_support.safe_url_for``'s own behavior/registration order were
    NOT touched.

STYLE/CSP IMPACT: ``weights.html`` carried one incidental fully-static
``style="min-width:250px;"`` attribute and one ``<style>`` block (its own
page-local CSS) -- independently measured via the canonical
``tests.security._bys360_style_inventory`` helper, not guessed. See
``tests/security/test_csp_style_migration_cumulative_inventory_contract.py``'s
FORWARD-COMPATIBILITY FOLLOW-UP 7 for the manifest entry and the list of
other test files whose hardcoded repo-wide totals needed the same
1-attribute/1-block adjustment (1035/225 -> 1034/224). ``template_safety.py``
carries no template markup, so Candidate B contributes 0 to this ledger.

This file writes NOTHING to app/template/CSS/config sources -- only
``Path.read_text()``/``Path.exists()``, ``git show``/``git cat-file`` (read-
only), and real, isolated Flask apps built via the repo's own ``create_app()``
against temporary, isolated SQLite DBs.
"""
from __future__ import annotations

import re
import subprocess
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Tip of phase5-critical-lint-clean-v1 immediately before this wave's own
# deletion/edit commits -- the repo state where weights.html and
# template_safety.safe_url_for both still existed.
PRE_DELETION_REF = "2838761cdc37d3c987ca6eb1ae1d2d0d0d9a1fff"

WEIGHTS_TEMPLATE = "app/templates/weights.html"
WEIGHTS_STALE_ENDPOINTS: tuple[str, ...] = (
    "main.performance_weight_create",
    "main.performance_weight_edit",
    "main.performance_weight_toggle_active",
    "main.performance_weight_delete",
)

# Same orphan family as weights.html -- explicitly OUT of scope for this
# wave, must remain present and byte-identical.
PRESERVED_SIBLING_ORPHANS: tuple[str, ...] = (
    "app/templates/weight_create.html",
    "app/templates/weight_edit.html",
)

TEMPLATE_SAFETY_MODULE = "app/template_safety.py"
ROUTE_SUPPORT_MODULE = "app/route_support.py"


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
# Candidate A -- weights.html: deletion contract.
# ---------------------------------------------------------------------------


def test_weights_html_is_genuinely_absent_from_worktree() -> None:
    assert not (REPO_ROOT / WEIGHTS_TEMPLATE).exists(), (
        f"{WEIGHTS_TEMPLATE} is claimed deleted by this wave but still exists on disk."
    )


def test_weights_html_existed_at_pre_deletion_ref() -> None:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{PRE_DELETION_REF}:{WEIGHTS_TEMPLATE}"],
        cwd=REPO_ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, (
        f"{WEIGHTS_TEMPLATE} does not appear to have existed at {PRE_DELETION_REF}: {result.stderr!r}"
    )


def test_weights_html_pre_deletion_content_referenced_all_four_stale_endpoints() -> None:
    """Independently re-derives the ORPHAN_CONFIRMED claim's own premise from
    the fixed pre-deletion git ref -- never just trusted."""
    text = _git_show(PRE_DELETION_REF, WEIGHTS_TEMPLATE).decode("utf-8")
    for endpoint in WEIGHTS_STALE_ENDPOINTS:
        assert f"safe_url_for('{endpoint}'" in text, (
            f"Pre-deletion {WEIGHTS_TEMPLATE} did not reference {endpoint!r} -- "
            "the ORPHAN_CONFIRMED premise for this wave would be wrong."
        )


def test_no_consumer_reference_to_weights_html_remains_in_app() -> None:
    offenders: list[str] = []
    for path in (REPO_ROOT / "app").rglob("*"):
        if not path.is_file() or path.suffix not in (".py", ".html", ".js"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "weights.html" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], f"Unexpected reference(s) to weights.html remain under app/: {offenders!r}"


def test_no_stale_weight_endpoint_string_remains_anywhere_in_app() -> None:
    offenders: list[str] = []
    for path in (REPO_ROOT / "app").rglob("*"):
        if not path.is_file() or path.suffix not in (".py", ".html"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(endpoint in text for endpoint in WEIGHTS_STALE_ENDPOINTS):
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], f"Stale weight endpoint string(s) unexpectedly found in: {offenders!r}"


@pytest.mark.parametrize("relative_path", PRESERVED_SIBLING_ORPHANS)
def test_preserved_sibling_orphan_template_is_untouched(relative_path: str) -> None:
    """weight_create.html / weight_edit.html are the same orphan family but
    explicitly out of this wave's scope -- must still exist, byte-identical
    to pre-wave (flagged separately as follow-up tech debt, not touched)."""
    current = _normalize_line_endings((REPO_ROOT / relative_path).read_bytes())
    pre_wave = _normalize_line_endings(_git_show(PRE_DELETION_REF, relative_path))
    assert current == pre_wave, f"{relative_path}: byte content changed since pre-wave ref -- must be untouched."


# ---------------------------------------------------------------------------
# Candidate B -- template_safety.safe_url_for: dead-helper removal contract.
# ---------------------------------------------------------------------------

_SAFE_URL_FOR_DEF_RE = re.compile(r"^def\s+safe_url_for\s*\(", re.MULTILINE)


def test_template_safety_no_longer_defines_safe_url_for() -> None:
    text = (REPO_ROOT / TEMPLATE_SAFETY_MODULE).read_text(encoding="utf-8")
    assert not _SAFE_URL_FOR_DEF_RE.search(text), (
        f"{TEMPLATE_SAFETY_MODULE} still defines safe_url_for -- expected removed (DEAD_SHADOWED_HELPER)."
    )
    assert "safe_url_for" not in text, (
        f"{TEMPLATE_SAFETY_MODULE} still references 'safe_url_for' somewhere (e.g. a leftover globals "
        "registration or import) -- expected fully removed."
    )


def test_template_safety_pre_deletion_content_defined_safe_url_for() -> None:
    """Independently re-derives the DEAD_SHADOWED_HELPER claim's own premise
    from the fixed pre-deletion git ref -- never just trusted."""
    text = _git_show(PRE_DELETION_REF, TEMPLATE_SAFETY_MODULE).decode("utf-8")
    assert _SAFE_URL_FOR_DEF_RE.search(text), (
        f"Pre-deletion {TEMPLATE_SAFETY_MODULE} did not define safe_url_for -- "
        "the DEAD_SHADOWED_HELPER premise for this wave would be wrong."
    )
    assert 'app.jinja_env.globals.setdefault("safe_url_for", safe_url_for)' in text


def test_route_support_safe_url_for_is_untouched() -> None:
    """This wave must not change route_support.safe_url_for's behavior or
    registration -- byte-identical to pre-wave."""
    current = _normalize_line_endings((REPO_ROOT / ROUTE_SUPPORT_MODULE).read_bytes())
    pre_wave = _normalize_line_endings(_git_show(PRE_DELETION_REF, ROUTE_SUPPORT_MODULE))
    assert current == pre_wave, f"{ROUTE_SUPPORT_MODULE}: byte content changed since pre-wave ref -- must be untouched."


def test_route_support_safe_url_for_is_the_sole_remaining_safe_url_for_definition() -> None:
    offenders: list[str] = []
    for path in (REPO_ROOT / "app").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if _SAFE_URL_FOR_DEF_RE.search(text):
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [str(Path(ROUTE_SUPPORT_MODULE))], (
        f"Expected exactly one 'def safe_url_for(' under app/ ({ROUTE_SUPPORT_MODULE}); found: {offenders!r}"
    )


def test_template_safety_no_longer_has_unused_url_for_import() -> None:
    text = (REPO_ROOT / TEMPLATE_SAFETY_MODULE).read_text(encoding="utf-8")
    assert "url_for" not in text, (
        f"{TEMPLATE_SAFETY_MODULE} still imports/references url_for, but no longer has any user of it."
    )


# ---------------------------------------------------------------------------
# Runtime proof: a real, isolated create_app() still renders safe_url_for
# calls correctly (via route_support's context-processor injection), and the
# now-removed Jinja global is genuinely gone from app.jinja_env.globals.
# ---------------------------------------------------------------------------

_TEST_DB_ROOT = Path("C:/bys360_pytest_tmp_final/weights_orphan_and_dead_helper_cleanup/test_dbs")


@pytest.fixture(scope="module")
def cleanup_wave_app():
    mp = pytest.MonkeyPatch()
    _TEST_DB_ROOT.mkdir(parents=True, exist_ok=True)
    db_path = _TEST_DB_ROOT / f"{uuid.uuid4().hex}.sqlite3"
    db_uri = "sqlite:///" + db_path.as_posix()

    mp.setenv("APP_ENV", "testing")
    mp.setenv("FLASK_ENV", "testing")
    mp.setenv("SECRET_KEY", "test-secret-key-for-weights-dead-helper-cleanup-min-length-ok")
    mp.setenv("DEFAULT_FIRST_LOGIN_PASSWORD", "test-password")
    mp.setenv("FLASK_SKIP_SCHEMA_VALIDATION", "1")
    mp.setenv("AUTO_REPAIR_SCHEMA", "false")
    mp.setenv("STRICT_SCHEMA_CHECK", "false")
    mp.setenv("REQUIRE_DOTENV_FILE", "false")
    mp.setenv("STRICT_ENV_VALIDATION", "false")
    mp.setenv("WTF_CSRF_ENABLED", "false")
    mp.setenv("DATABASE_URL", db_uri)
    mp.setenv("MAIL_SUPPRESS_SEND", "true")
    mp.setenv("SCHEDULER_ENABLED", "false")

    from app import create_app
    from config import Config

    mp.setattr(Config, "APP_ENV", "testing")
    mp.setattr(Config, "SQLALCHEMY_DATABASE_URI", db_uri)
    mp.setattr(Config, "SQLALCHEMY_ENGINE_OPTIONS", {})

    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, SQLALCHEMY_DATABASE_URI=db_uri)

    from app.extensions import db

    with app.app_context():
        db.create_all()

    yield app
    mp.undo()


def test_jinja_env_globals_no_longer_carries_safe_url_for(cleanup_wave_app) -> None:
    assert cleanup_wave_app.jinja_env.globals.get("safe_url_for") is None, (
        "app.jinja_env.globals['safe_url_for'] should be gone now that template_safety's dead "
        "registration was removed."
    )


def test_real_template_render_still_resolves_safe_url_for_to_route_support(cleanup_wave_app) -> None:
    """Proves this wave's removal is safe: templates that call safe_url_for()
    still work, and the function that actually executes is (and always was)
    app.route_support.safe_url_for -- unaffected by removing the dead
    shadowed Jinja global."""
    from flask import render_template_string

    with cleanup_wave_app.test_request_context("/"):
        identity = render_template_string("{{ safe_url_for.__module__ }}.{{ safe_url_for.__qualname__ }}")
        resolved_url = render_template_string("{{ safe_url_for('main.login') }}")

    assert identity == "app.route_support.safe_url_for", (
        f"Rendered safe_url_for identity is {identity!r}; expected app.route_support.safe_url_for."
    )
    assert resolved_url and resolved_url != "#", (
        f"safe_url_for('main.login') rendered {resolved_url!r}; expected a real resolved URL, not the "
        "BuildError fallback."
    )


def test_url_map_route_count_is_unchanged(cleanup_wave_app) -> None:
    total = len(list(cleanup_wave_app.url_map.iter_rules()))
    assert total == 985, f"url_map route count is {total}; expected 985 (unchanged -- neither candidate touched routes)."


def test_successor_hierarchy_settings_route_is_unaffected(cleanup_wave_app) -> None:
    """The nearest live route touching the same underlying weight data
    (explicitly NOT treated as a true successor -- see module docstring)
    must remain registered and untouched by this wave."""
    rules_by_endpoint = {rule.endpoint: rule for rule in cleanup_wave_app.url_map.iter_rules()}
    assert "main.performance_hierarchy_settings" in rules_by_endpoint


# ---------------------------------------------------------------------------
# Scope guard: this wave introduces no xfail and writes to nothing outside
# the intended files.
# ---------------------------------------------------------------------------

_XFAIL_CALL_RE = re.compile(r"pytest" + r"\.xfail\(")
_XFAIL_MARK_RE = re.compile(r"@pytest" + r"\.mark\.xfail")


def test_this_file_introduces_no_xfail_usage() -> None:
    own_text = Path(__file__).read_text(encoding="utf-8")
    call_count = len(_XFAIL_CALL_RE.findall(own_text))
    mark_count = len(_XFAIL_MARK_RE.findall(own_text))
    assert call_count + mark_count == 0, (
        f"This test-only file must not introduce any real xfail usage (found "
        f"{call_count} xfail-call usages and {mark_count} xfail-mark-decorator usages)."
    )
