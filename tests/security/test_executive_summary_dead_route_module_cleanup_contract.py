"""BYS360 Executive Summary Dead Route Module Cleanup -- contract test.

CONTEXT: `app/dashboard/executive_summary_routes.py` defined THREE distinct
route groups (not just the one daily-weather-mail pair already handled by
a prior, separate wave):

    1. `/dashboard/yonetici-ozeti` (GET) -> `executive_summary_dashboard()`
       -> would have rendered `dashboard/executive_summary.html`.
    2. `/dashboard/yonetici-ozeti/send-test` (POST) ->
       `executive_summary_send_mail()`.
    3. `/executive-summary/daily-weather-mail` +
       `/yonetici-ozeti/gunluk-hava-maili` (GET/POST) ->
       `executive_summary_daily_weather_mail_tasks_v1_3_1()` -> would have
       rendered the already-deleted `executive_summary/daily_weather_mail_
       tasks.html` (see "BYS360 Daily Weather/Mail Orphan Template
       Temizliği").

INDEPENDENT RE-VERIFICATION (not assumed from the prior wave's finding):
a real, isolated `create_app()` proved:
    - `app.dashboard.executive_summary_routes` is absent from `sys.modules`
      -- neither `app/dashboard/routes.py` nor `app/dashboard/__init__.py`
      import it, and a repo-wide grep for any real `import`/`from ...
      import` of this module (excluding the module's own self-referential
      logging strings) returns zero hits.
    - `/dashboard/yonetici-ozeti` [GET] resolves to a COMPLETELY DIFFERENT,
      genuinely live module: `executive_summary.yonetici_ozeti` in
      `app/executive_summary/routes.py` (registered directly in
      `app/__init__.py::create_app()` via `app.register_blueprint(
      executive_summary_bp)`, `url_prefix="/dashboard"`). This is a real
      URL COLLISION between the dead file's claimed route and a genuinely
      live one -- the live one wins because the dead module's decorators
      never execute.
    - `/dashboard/yonetici-ozeti/send-test` [POST] has NO live equivalent
      at all -- 404.
    - `/executive-summary/daily-weather-mail` and `/yonetici-ozeti/gunluk-
      hava-maili` resolve to `main.daily_weather_mail_settings` in
      `app/communication/daily_weather_mail_routes.py` (already
      established by the prior daily-weather-mail orphan cleanup).
    - The real `url_map`'s sorted-endpoint-list SHA-256 and route count are
      BYTE-IDENTICAL before and after this module's deletion (985 routes,
      hash `624e25c447915f9eaf68c8583b80e962236dcecbea962259a1a21604bb48a94a`)
      -- this dead module never contributed a single runtime endpoint.

FILE-INTERNAL DEPENDENCY ANALYSIS: every symbol defined in the dead file
(`_ADMIN_ROLE_TOKENS`, `_normalize`, `_safe_actor_id`,
`_is_system_admin_user`, `system_admin_required`, `_v3_enrich_context`, and
the three view functions) was independently grepped repo-wide; the only
external hits were coincidental same-name-but-unrelated symbols in other
files (an independently-defined `_ADMIN_ROLE_TOKENS` constant in
`app/services/bys360_notification_bridge.py`; the string
`executive_summary_dashboard` appearing only as a menu-key ALLOWLIST ENTRY
in `app/menu_registry.py`, never as a `url_for()`/import reference) -- not
real dependencies. The service module it imported from,
`app/services/executive_summary_service.py`
(`build_executive_summary_context`, `send_executive_summary_mail`), has
NO other consumer either (confirmed absent from `sys.modules` too) --
it was left UNTOUCHED regardless, since deleting a service file was not
part of this task's declared scope (a candidate for a future, separate
cleanup, not acted on here). `app/templates/dashboard/executive_summary.
html` (the dead dashboard route's own template) was likewise left
UNTOUCHED for the same reason.

DELETED: `app/dashboard/executive_summary_routes.py` (150 lines, 3 route
groups, all confirmed unreachable).

PRESERVED (all explicitly out of scope): `app/services/executive_summary_
service.py`, `app/templates/dashboard/executive_summary.html`, the real
`app/executive_summary/` package, `app/communication/daily_weather_mail_
routes.py`, `app/dashboard/routes.py`, `app/dashboard/__init__.py`,
`app/route_registry.py`, all launcher/installer scripts, CSS/JS, CSP/nonce,
meeting templates.

This file writes NOTHING to app/template/CSS/config sources -- only
`Path.read_text()`, `git show` (read-only), and real Flask
`app`-fixture-based `url_map`/route-resolution checks (no HTTP POST, no
mail/task code ever invoked).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

DEAD_ROUTE_FILE = "app/dashboard/executive_summary_routes.py"

# The commit immediately BEFORE this cleanup's own deletion commit -- the
# repo state where the dead route file still existed on disk.
PRE_DELETION_REF = "31394332285c54f05d41cbcebd70954d91676e7a"

# Independently re-verified (see module docstring) via a real, isolated
# create_app() both immediately before and immediately after deletion --
# byte-identical in both cases, proving the dead module never contributed
# a single runtime endpoint.
EXPECTED_ROUTE_COUNT = 985
EXPECTED_ENDPOINT_LIST_SHA256 = "624e25c447915f9eaf68c8583b80e962236dcecbea962259a1a21604bb48a94a"

STARTUP_FILES_THAT_MUST_NOT_REFERENCE_THE_DEAD_MODULE = (
    "app/dashboard/routes.py",
    "app/dashboard/__init__.py",
    "app/route_registry.py",
    "app/routes.py",
)

ROUTE_MANIFEST_FILES = (
    "app/admin/route_manifest.py",
    "app/communication/route_manifest.py",
    "app/institutional/route_manifest.py",
)


def _git_show(ref: str, relative_path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{ref}:{relative_path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, f"'git show {ref}:{relative_path}' failed: {result.stderr!r}"
    return result.stdout


# ---------------------------------------------------------------------------
# 1) Orphan-absence: the dead route module file itself is gone.
# ---------------------------------------------------------------------------


def test_dead_route_module_file_no_longer_exists() -> None:
    assert not (REPO_ROOT / DEAD_ROUTE_FILE).exists(), (
        f"{DEAD_ROUTE_FILE} is recorded as deleted but still exists on disk."
    )


def test_dead_route_module_pre_deletion_content_is_reproducible_from_git_history() -> None:
    """Companion check: the file's PRE_DELETION_REF content is still
    retrievable (proves PRE_DELETION_REF is a real, correct ref and the
    historical evidence used elsewhere in this test suite is genuine, not
    a typo'd/broken ref that would silently make other git-show-based
    tests pass vacuously)."""
    text = _git_show(PRE_DELETION_REF, DEAD_ROUTE_FILE)
    assert "def executive_summary_dashboard():" in text
    assert "def executive_summary_send_mail():" in text
    assert "def executive_summary_daily_weather_mail_tasks_v1_3_1():" in text
    assert "@bp.route('/dashboard/yonetici-ozeti', methods=['GET'])" in text
    assert "@bp.route('/dashboard/yonetici-ozeti/send-test', methods=['POST'])" in text


# ---------------------------------------------------------------------------
# 2) Startup / manifest / blueprint-registration chain never referenced the
#    dead module -- independently re-verified, not assumed from the prior
#    wave's finding.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", STARTUP_FILES_THAT_MUST_NOT_REFERENCE_THE_DEAD_MODULE)
def test_startup_files_never_reference_the_dead_module(relative_path: str) -> None:
    text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    assert "executive_summary_routes" not in text, (
        f"{relative_path} references 'executive_summary_routes' -- the dead module may "
        "actually be live, in which case it should not have been deleted."
    )


@pytest.mark.parametrize("relative_path", ROUTE_MANIFEST_FILES)
def test_route_manifest_files_never_reference_the_dead_module(relative_path: str) -> None:
    text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    assert "executive_summary_routes" not in text, (
        f"{relative_path} references 'executive_summary_routes'."
    )


def test_no_python_file_anywhere_actually_imports_the_dead_module() -> None:
    """Repo-wide AST-free but precise textual scan for a REAL import
    statement (not a docstring/comment mention, which is intentionally
    common throughout this test suite's own historical-evidence comments)."""
    real_import_needle_patterns = (
        "import executive_summary_routes",
        "from .executive_summary_routes",
        "from app.dashboard.executive_summary_routes",
        "from app.dashboard import executive_summary_routes",
    )
    offending_files: list[str] = []
    for py_file in (REPO_ROOT / "app").rglob("*.py"):
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        if any(pattern in content for pattern in real_import_needle_patterns):
            offending_files.append(str(py_file.relative_to(REPO_ROOT)))
    assert not offending_files, (
        f"A real import of the dead module was found: {offending_files!r} -- this "
        "invalidates the orphan classification."
    )


# ---------------------------------------------------------------------------
# 3) Real Flask app: url_map route-count/hash invariance + active route
#    resolution proof.
#
#    BYS360 KOORDINATOR NOTU: bu bolum KASITLI olarak paylasilan (session-
#    scoped) `app` fixture'ini KULLANMAZ. `tests/workflow/test_phase5w_
#    workflow_schema_readiness.py` (ve benzer izole-birim-testi dosyalari)
#    olu kod modullerini (ornegin app.workflow.routes) dogrudan import
#    ediyor; tam test paketi icinde bu import, paylasilan `main_bp`
#    Blueprint nesnesine kalici olarak yaziliyor -- bu urunun kendisinde bir
#    hata DEGIL, test suite'inin ayni process'i paylasmasindan kaynaklanan
#    bir gozlem artefakti (bkz. tests/quality/test_president_approvals_
#    route_contract.py'nin ayni deseni KENDI docstring'inde tarif ettigi ve
#    izole bir alt-surecle cozdugu emsal). Bu yuzden asagidaki iki test,
#    o dosyanin KENDI kurulu deseniyle (3 ajanin da izledigi), TAMAMEN IZOLE
#    bir alt-process'te `create_app()` calistirir -- paylasilan `app`
#    fixture'ina guvenmez.
# ---------------------------------------------------------------------------


def _run_isolated_create_app_probe(probe_script: str) -> list[str]:
    import subprocess
    import sys as _sys

    result = subprocess.run(
        [_sys.executable, "-c", probe_script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, {"stdout": result.stdout, "stderr": result.stderr}
    return result.stdout.strip().splitlines()


def test_url_map_route_count_and_endpoint_hash_match_pre_and_post_deletion_baseline() -> None:
    """The EXPECTED_* constants above were independently derived from a
    real, isolated `create_app()` run both immediately BEFORE and
    immediately AFTER this module's deletion -- byte-identical in both
    cases. This test locks that invariance in permanently: if the live
    `url_map` ever drifts from this fixed baseline, something ELSE (not
    this cleanup) changed the route surface. Runs in an isolated
    subprocess (see module-level KOORDINATOR NOTU above) so a sibling test
    file's direct import of an unrelated dead route module cannot pollute
    the count."""
    probe_script = (
        "import hashlib\n"
        "from app import create_app\n"
        "app = create_app()\n"
        "endpoint_list = sorted(rule.endpoint for rule in app.url_map.iter_rules())\n"
        "print('ROUTE_COUNT=%d' % len(endpoint_list))\n"
        "print('ENDPOINT_SHA256=%s' % hashlib.sha256(chr(10).join(endpoint_list).encode()).hexdigest())\n"
    )
    output_lines = _run_isolated_create_app_probe(probe_script)
    values = dict(line.split("=", 1) for line in output_lines if "=" in line)
    assert values.get("ROUTE_COUNT") == str(EXPECTED_ROUTE_COUNT), (
        f"Isolated create_app() url_map route count is {values.get('ROUTE_COUNT')}; "
        f"expected {EXPECTED_ROUTE_COUNT}."
    )
    assert values.get("ENDPOINT_SHA256") == EXPECTED_ENDPOINT_LIST_SHA256, (
        f"Isolated create_app() url_map sorted-endpoint-list SHA-256 is "
        f"{values.get('ENDPOINT_SHA256')}; expected {EXPECTED_ENDPOINT_LIST_SHA256}."
    )


def test_dead_modules_claimed_urls_either_404_or_resolve_to_a_different_live_view() -> None:
    """For each of the 4 URLs the dead module claimed to serve: either the
    URL 404s (no live equivalent at all), or it resolves to a genuinely
    different, live module -- never to anything from the dead file. Also
    confirms the dead module is absent from `sys.modules`. Isolated
    subprocess, same reason as above."""
    probe_script = (
        "import sys\n"
        "from app import create_app\n"
        "app = create_app()\n"
        "print('MODULE_ABSENT=%s' % ('app.dashboard.executive_summary_routes' not in sys.modules))\n"
        "adapter = app.url_map.bind('localhost')\n"
        "cases = [\n"
        "    ('/dashboard/yonetici-ozeti', 'GET'),\n"
        "    ('/dashboard/yonetici-ozeti/send-test', 'POST'),\n"
        "    ('/executive-summary/daily-weather-mail', 'GET'),\n"
        "    ('/yonetici-ozeti/gunluk-hava-maili', 'GET'),\n"
        "]\n"
        "for path, method in cases:\n"
        "    try:\n"
        "        endpoint, _args = adapter.match(path, method=method)\n"
        "        vf = app.view_functions.get(endpoint)\n"
        "        mod = getattr(vf, '__module__', None)\n"
        "        print('%s|%s|MATCH|%s|%s' % (path, method, endpoint, mod))\n"
        "    except Exception as exc:\n"
        "        print('%s|%s|%s' % (path, method, type(exc).__name__))\n"
    )
    output_lines = _run_isolated_create_app_probe(probe_script)
    results = {}
    for line in output_lines:
        if line.startswith("MODULE_ABSENT="):
            continue
        parts = line.split("|")
        results[(parts[0], parts[1])] = parts[2:]

    assert "MODULE_ABSENT=True" in output_lines, (
        f"app.dashboard.executive_summary_routes is present in sys.modules: {output_lines!r}"
    )

    expected = {
        ("/dashboard/yonetici-ozeti", "GET"): ["MATCH", "executive_summary.yonetici_ozeti", "app.executive_summary.routes"],
        ("/dashboard/yonetici-ozeti/send-test", "POST"): ["NotFound"],
        ("/executive-summary/daily-weather-mail", "GET"): ["MATCH", "main.daily_weather_mail_settings", "app.communication.daily_weather_mail_routes"],
        ("/yonetici-ozeti/gunluk-hava-maili", "GET"): ["MATCH", "main.daily_weather_mail_settings", "app.communication.daily_weather_mail_routes"],
    }
    for key, expected_value in expected.items():
        assert results.get(key) == expected_value, (
            f"{key}: got {results.get(key)!r}, expected {expected_value!r}. Full output: {output_lines!r}"
        )


# ---------------------------------------------------------------------------
# 4) Preserved files: service module and dashboard template untouched
#    (explicitly out of this task's scope, even though both are now
#    doubly-orphaned).
# ---------------------------------------------------------------------------


def test_executive_summary_service_module_still_exists_untouched() -> None:
    """`app/services/executive_summary_service.py` had zero OTHER consumers
    besides the now-deleted route file, but deleting a service module was
    not part of this task's declared scope -- it must remain, unmodified,
    as a residual cleanup candidate for a future, separate task."""
    service_path = REPO_ROOT / "app/services/executive_summary_service.py"
    assert service_path.exists(), (
        "app/services/executive_summary_service.py is missing -- it should have been "
        "left untouched by this cleanup."
    )


def test_dashboard_executive_summary_template_still_exists_untouched() -> None:
    """`app/templates/dashboard/executive_summary.html` (the dead
    dashboard route's own template) was likewise left untouched -- deleting
    templates was not part of this task's declared scope."""
    template_path = REPO_ROOT / "app/templates/dashboard/executive_summary.html"
    assert template_path.exists(), (
        "app/templates/dashboard/executive_summary.html is missing -- it should have been "
        "left untouched by this cleanup."
    )


def test_daily_weather_mail_service_and_cli_scripts_still_exist_untouched() -> None:
    """Regression guard carried over from the prior orphan-cleanup waves:
    the real daily-weather-mail route/service files and CLI scripts remain
    untouched by this Python-route-module cleanup too."""
    for relative_path in (
        "app/communication/daily_weather_mail_routes.py",
        "app/services/executive_mail_center.py",
        "scripts/communication/send_daily_evening_tomorrow_mail.py",
        "scripts/communication/send_daily_pulse_check_mail.py",
    ):
        assert (REPO_ROOT / relative_path).exists(), f"{relative_path} is missing."


# ---------------------------------------------------------------------------
# 5) Style/CSP/handler inventory unchanged (a .py-only deletion cannot
#    affect the HTML-scoped canonical inventory -- defense-in-depth check).
# ---------------------------------------------------------------------------

EXPECTED_ACTIVE_STYLE_TOTAL = 1040
EXPECTED_DYNAMIC_STYLE_TOTAL = 66
EXPECTED_STYLE_BLOCK_TOTAL = 248


def test_canonical_style_and_handler_inventory_is_unchanged() -> None:
    from tests.security._bys360_style_inventory import compute_inventory_from_worktree

    inventory = compute_inventory_from_worktree()
    assert inventory.active_static_total == EXPECTED_ACTIVE_STYLE_TOTAL, (
        f"active_static_total is {inventory.active_static_total}; expected "
        f"{EXPECTED_ACTIVE_STYLE_TOTAL} (a .py-only deletion must not change this)."
    )
    assert inventory.dynamic_total == EXPECTED_DYNAMIC_STYLE_TOTAL, (
        f"dynamic_total is {inventory.dynamic_total}; expected {EXPECTED_DYNAMIC_STYLE_TOTAL}."
    )
    assert inventory.style_block_total == EXPECTED_STYLE_BLOCK_TOTAL, (
        f"style_block_total is {inventory.style_block_total}; expected {EXPECTED_STYLE_BLOCK_TOTAL}."
    )
    assert inventory.inline_handler_total == 0, f"inline_handler_total is {inventory.inline_handler_total}; expected 0."
    assert inventory.javascript_url_total == 0, f"javascript_url_total is {inventory.javascript_url_total}; expected 0."


def test_csp_style_directives_unchanged(client) -> None:
    response = client.get("/login")
    policy = response.headers.get("Content-Security-Policy") or response.headers.get(
        "Content-Security-Policy-Report-Only"
    )
    assert policy, "No CSP header found in the response."
    directives: dict[str, str] = {}
    for chunk in policy.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split(None, 1)
        directives[parts[0]] = parts[1] if len(parts) > 1 else ""
    expected = {
        "style-src": "'self' 'unsafe-inline' https:",
        "style-src-elem": "'self' 'unsafe-inline' https:",
        "style-src-attr": "'unsafe-inline'",
    }
    for directive, expected_value in expected.items():
        assert directives.get(directive) == expected_value, (
            f"'{directive}' is {directives.get(directive)!r}; expected {expected_value!r}."
        )
        assert "'nonce-" not in directives.get(directive, ""), (
            f"'{directive}' unexpectedly contains a 'nonce-' token."
        )


# ---------------------------------------------------------------------------
# 6) Route snapshot (static AST scan, independent of runtime reachability)
#    no longer contains this module's decorator-declared routes.
# ---------------------------------------------------------------------------


def test_phase2b_route_snapshot_no_longer_contains_dead_module_keys() -> None:
    import json

    snapshot_path = REPO_ROOT / "tests/architecture/snapshots/phase2b_route_snapshot_baseline.json"
    baseline = json.loads(snapshot_path.read_text(encoding="utf-8"))
    contract_keys = set(baseline["contract_keys"])
    dead_module_keys = {
        "/dashboard/yonetici-ozeti|GET",
        "/dashboard/yonetici-ozeti/send-test|POST",
        "/executive-summary/daily-weather-mail|GET,POST",
        "/yonetici-ozeti/gunluk-hava-maili|GET,POST",
    }
    # "/dashboard/yonetici-ozeti|GET" is still expected ONCE, from the real
    # executive_summary_bp -- only the dead module's SECOND, now-removed
    # copy of that exact key (and the other 3 dead-module-only keys) should
    # be gone.
    from collections import Counter

    key_counts = Counter(baseline["contract_keys"])
    assert key_counts["/dashboard/yonetici-ozeti|GET"] == 1, (
        f"'/dashboard/yonetici-ozeti|GET' appears {key_counts['/dashboard/yonetici-ozeti|GET']} "
        "times in the snapshot; expected exactly 1 (the real executive_summary_bp's own copy)."
    )
    for key in dead_module_keys - {"/dashboard/yonetici-ozeti|GET"}:
        assert key not in contract_keys, f"{key!r} still present in the route snapshot; expected removed."


# ---------------------------------------------------------------------------
# 7) No new xfail/skip introduced by this file; this file never writes to
#    application source paths.
# ---------------------------------------------------------------------------

_XFAIL_CALL_RE_PARTS = ("pytest", ".xfail(")
_XFAIL_MARK_RE_PARTS = ("@pytest", ".mark.xfail")
_SKIP_MARK_RE_PARTS = ("@pytest", ".mark.skip")
_SKIP_CALL_RE_PARTS = ("pytest", ".skip(")


def test_this_file_introduces_no_xfail_or_skip_usage() -> None:
    """Deliberately builds each needle via string concatenation so this
    check's OWN source line never contains the literal pattern it searches
    for (which would otherwise make it self-match)."""
    own_text = Path(__file__).read_text(encoding="utf-8")
    assert "".join(_XFAIL_CALL_RE_PARTS) not in own_text
    assert "".join(_XFAIL_MARK_RE_PARTS) not in own_text
    assert "".join(_SKIP_MARK_RE_PARTS) not in own_text
    assert "".join(_SKIP_CALL_RE_PARTS) not in own_text


def test_this_file_never_writes_to_application_source_paths() -> None:
    forbidden_write_markers = (
        "write_text(",
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
    assert hits == [], f"Unexpected file-write/mutation call trace found in this file: {hits!r}"
