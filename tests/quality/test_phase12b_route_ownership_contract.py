"""Phase 12B strategic, manifest, and source-only route ownership contracts.

The Phase 12B audit found no production route or module removal that satisfies
the repository's SAFE threshold. These tests lock the observed runtime state
and the concrete reasons why the candidates must not be treated as identical
duplicates without a later product/ownership decision.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

import pytest
from flask import url_for
from werkzeug.exceptions import NotFound

pytestmark = pytest.mark.ci_safe

REPO_ROOT = Path(__file__).resolve().parents[2]


class _StrategicConflict(TypedDict):
    methods: set[str]
    winner: str
    shadowed: str
    indexes: tuple[int, int]


STRATEGIC_CONFLICTS: dict[str, _StrategicConflict] = {
    "/performans/stratejik/kpi-dashboard": {
        "methods": {"GET"},
        "winner": "main.sp1_kpi_dashboard_tr",
        "shadowed": "strategic_performance.kpi_dashboard",
        "indexes": (798, 878),
    },
    "/performans/stratejik/hedefler": {
        "methods": {"GET"},
        "winner": "main.sp1_kpi_targets_tr",
        "shadowed": "strategic_performance.target_list",
        "indexes": (800, 880),
    },
    "/performans/stratejik/yetkinlik-kutuphanesi": {
        "methods": {"GET"},
        "winner": "main.sp1_competency_library_tr",
        "shadowed": "strategic_performance.competency_library",
        "indexes": (806, 879),
    },
    "/performans/stratejik/oz-degerlendirme": {
        "methods": {"GET", "POST"},
        "winner": "main.sp1_self_review_tr",
        "shadowed": "strategic_performance.self_review",
        "indexes": (808, 883),
    },
    "/performans/stratejik/ai-kpi-analiz": {
        "methods": {"GET"},
        "winner": "main.sp1_ai_kpi_analysis_tr",
        "shadowed": "strategic_performance.ai_kpi_analysis",
        "indexes": (810, 884),
    },
}


def _raw_endpoint_response(app, endpoint: str):
    with app.test_request_context("/manifest.webmanifest"):
        response = app.make_response(app.view_functions[endpoint]())
        response.direct_passthrough = False
        response.get_data()
        return response


@pytest.fixture(scope="module")
def fresh_runtime_snapshot(tmp_path_factory):
    """Measure exact production route state outside collection-time blueprint contamination."""
    runtime_root = tmp_path_factory.mktemp("phase12b-fresh-runtime")
    probe = """
import json
from collections import defaultdict
from app import create_app

paths = [
    "/performans/stratejik/kpi-dashboard",
    "/performans/stratejik/hedefler",
    "/performans/stratejik/yetkinlik-kutuphanesi",
    "/performans/stratejik/oz-degerlendirme",
    "/performans/stratejik/ai-kpi-analiz",
    "/manifest.webmanifest",
]
automatic = {"HEAD", "OPTIONS"}

def snapshot(app):
    rules = list(app.url_map.iter_rules())
    entries = {
        path: [
            {
                "index": index,
                "endpoint": rule.endpoint,
                "methods": sorted(set(rule.methods or ()) - automatic),
            }
            for index, rule in enumerate(rules)
            if rule.rule == path
        ]
        for path in paths
    }
    adapter = app.url_map.bind("localhost", url_scheme="http")
    winners = {}
    for path in paths:
        methods = ["GET", "POST"] if path.endswith("oz-degerlendirme") else ["GET"]
        for method in methods:
            winners[f"{path}|{method}"] = adapter.match(path, method=method)[0]

    grouped = defaultdict(list)
    for rule in rules:
        grouped[rule.rule].append(
            (rule.endpoint, set(rule.methods or ()) - automatic)
        )
    conflicts = []
    for path, path_entries in grouped.items():
        per_endpoint = defaultdict(set)
        for endpoint, methods in path_entries:
            per_endpoint[endpoint] |= methods
        endpoints = list(per_endpoint)
        if any(
            per_endpoint[left] & per_endpoint[right]
            for index, left in enumerate(endpoints)
            for right in endpoints[index + 1:]
        ):
            conflicts.append(path)
    return {
        "counts": [
            len(rules),
            len({rule.rule for rule in rules}),
            len({rule.endpoint for rule in rules}),
        ],
        "entries": entries,
        "winners": winners,
        "conflicts": sorted(conflicts),
    }

first = create_app()
second = create_app()
print(json.dumps({"first": snapshot(first), "second": snapshot(second)}))
"""
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["LOG_FOLDER"] = str(runtime_root / "logs")
    env["LOG_LEVEL"] = "CRITICAL"
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, {"stdout": result.stdout, "stderr": result.stderr}
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_strategic_conflict_matrix_and_registration_indexes_are_locked(
    fresh_runtime_snapshot,
):
    runtime = fresh_runtime_snapshot["first"]

    for path, expected in STRATEGIC_CONFLICTS.items():
        entries = runtime["entries"][path]
        assert [(entry["index"], entry["endpoint"]) for entry in entries] == [
            (expected["indexes"][0], expected["winner"]),
            (expected["indexes"][1], expected["shadowed"]),
        ]
        assert all(set(entry["methods"]) == expected["methods"] for entry in entries)
        for method in expected["methods"]:
            assert runtime["winners"][f"{path}|{method}"] == expected["winner"]


def test_strategic_handlers_have_reviewed_business_contract_differences():
    main_source = (
        REPO_ROOT / "app" / "performance" / "sp1_sidebar_routes.py"
    ).read_text(encoding="utf-8")
    strategic_source = (
        REPO_ROOT / "app" / "modules" / "strategic_performance" / "routes.py"
    ).read_text(encoding="utf-8")
    sp1c_source = (
        REPO_ROOT / "app" / "services" / "sp1c_kpi_dashboard_service.py"
    ).read_text(encoding="utf-8")
    sp3a_source = (
        REPO_ROOT / "app" / "services" / "sp3a_kpi_dashboard_live_service.py"
    ).read_text(encoding="utf-8")

    assert "build_sp1c_kpi_dashboard_context(current_user)" in main_source
    assert "build_sp3a_kpi_dashboard_context(current_user)" in strategic_source
    assert "LIMIT 20" in sp1c_source
    assert "LIMIT 50" in sp3a_source
    assert "weighted_completion" not in sp1c_source
    assert "weighted_completion" in sp3a_source
    assert "safe_render(" in main_source
    assert 'redirect(url_for("main.sp1_self_review"))' in main_source
    assert 'redirect(url_for("strategic_performance.self_review"))' in strategic_source


def test_strategic_menu_endpoints_resolve_to_shadowed_names_but_main_wins(app):
    menu_source = (REPO_ROOT / "app" / "menu_registry.py").read_text(encoding="utf-8")
    adapter = app.url_map.bind("localhost", url_scheme="http")

    with app.test_request_context():
        for path, expected in STRATEGIC_CONFLICTS.items():
            shadowed = expected["shadowed"]
            assert shadowed in menu_source or path.endswith(("oz-degerlendirme", "ai-kpi-analiz"))
            if shadowed in app.view_functions:
                generated_path = url_for(shadowed)
                assert generated_path in {
                    path,
                    "/performans/stratejik/kpi-analiz",
                }
            endpoint, _values = adapter.match(path, method="GET")
            assert endpoint == expected["winner"]

    alias_endpoint, _values = adapter.match(
        "/performans/stratejik/kpi-analiz",
        method="GET",
    )
    assert alias_endpoint == "strategic_performance.ai_kpi_analysis"


def test_manifest_winner_and_route_snapshot_are_deterministic_across_factories(
    fresh_runtime_snapshot,
):
    expected_snapshot = [985, 960, 880]

    for runtime in fresh_runtime_snapshot.values():
        assert runtime["counts"] == expected_snapshot
        entries = runtime["entries"]["/manifest.webmanifest"]
        assert [(entry["index"], entry["endpoint"]) for entry in entries] == [
            (812, "main.bys360_pwa_manifest"),
            (906, "pwa.manifest_webmanifest"),
        ]
        assert (
            runtime["winners"]["/manifest.webmanifest|GET"]
            == "main.bys360_pwa_manifest"
        )


def test_manifest_raw_handler_bodies_match_but_header_contracts_differ(app):
    main_response = _raw_endpoint_response(app, "main.bys360_pwa_manifest")
    pwa_response = _raw_endpoint_response(app, "pwa.manifest_webmanifest")

    assert main_response.status_code == pwa_response.status_code == 200
    assert main_response.mimetype == pwa_response.mimetype == "application/manifest+json"
    assert main_response.get_data() == pwa_response.get_data()
    assert main_response.headers["Cache-Control"] == pwa_response.headers["Cache-Control"]
    assert main_response.headers.get("Last-Modified") == pwa_response.headers.get(
        "Last-Modified"
    )
    assert main_response.headers.get("ETag")
    assert pwa_response.headers.get("ETag")
    assert main_response.headers.get("Pragma") is None
    assert main_response.headers.get("X-Content-Type-Options") is None
    assert pwa_response.headers["Pragma"] == "no-cache"
    assert pwa_response.headers["X-Content-Type-Options"] == "nosniff"


def test_manifest_public_response_and_conditional_cache_contract(client):
    manifest_path = REPO_ROOT / "app" / "static" / "pwa" / "manifest.webmanifest"
    response = client.get("/manifest.webmanifest")

    assert response.status_code == 200
    assert response.mimetype == "application/manifest+json"
    assert response.data == manifest_path.read_bytes()
    assert response.headers["Cache-Control"] == "no-cache, no-store, must-revalidate"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers.get("ETag")
    assert response.headers.get("Last-Modified")

    manifest = response.get_json()
    assert manifest["start_url"] == "/?source=pwa"
    assert manifest["scope"] == "/"
    assert manifest["display"] == "standalone"
    assert manifest["background_color"] == "#f7f8fb"
    assert manifest["theme_color"] == "#8B0000"
    assert len(manifest["icons"]) == 13
    assert len(manifest["shortcuts"]) == 3

    etag_response = client.get(
        "/manifest.webmanifest",
        headers={"If-None-Match": response.headers["ETag"]},
    )
    modified_response = client.get(
        "/manifest.webmanifest",
        headers={"If-Modified-Since": response.headers["Last-Modified"]},
    )
    assert etag_response.status_code == 304
    assert modified_response.status_code == 304


def test_manifest_missing_file_behavior_is_intentionally_not_equivalent(
    app,
    monkeypatch,
    tmp_path,
):
    from app.pwa import routes as pwa_routes

    missing_static = tmp_path / "missing-static"
    monkeypatch.setattr(app, "static_folder", str(missing_static))
    monkeypatch.setattr(pwa_routes, "_pwa_dir", lambda: missing_static / "pwa")

    with app.test_request_context("/manifest.webmanifest"):
        with pytest.raises(NotFound):
            app.view_functions["main.bys360_pwa_manifest"]()

        fallback = app.make_response(app.view_functions["pwa.manifest_webmanifest"]())
        assert fallback.status_code == 200
        assert fallback.mimetype == "application/manifest+json"
        assert json.loads(fallback.get_data(as_text=True))["icons"] == []


def test_manifest_link_and_both_live_service_worker_contracts_remain_present(app):
    base_template = (REPO_ROOT / "app" / "templates" / "base.html").read_text(
        encoding="utf-8"
    )
    registration_script = (
        REPO_ROOT / "app" / "static" / "js" / "bys360_ios_pwa_v2.js"
    ).read_text(encoding="utf-8")
    adapter = app.url_map.bind("localhost", url_scheme="http")

    assert '<link rel="manifest" href="/manifest.webmanifest">' in base_template
    assert "/service-worker.js" in registration_script
    assert adapter.match("/service-worker.js", method="GET")[0] == "pwa.service_worker_js"
    assert (
        adapter.match("/bys360-sw.js", method="GET")[0]
        == "main.bys360_pwa_service_worker"
    )


def test_source_only_route_candidates_are_absent_from_fresh_production_runtime(tmp_path):
    probe = """
import json
import sys
from app import create_app

app = create_app()
candidates = [
    "app.workflow.routes",
    "app.routes_president_scorecard_v2",
    "app.workflow.dashboard_upgrade_routes",
    "app.pwa_blueprint",
    "app.pwa_routes",
]
payload = {
    "loaded": {name: name in sys.modules for name in candidates},
    "blueprints": sorted(app.blueprints),
    "endpoints": sorted(rule.endpoint for rule in app.url_map.iter_rules()),
}
print(json.dumps(payload))
"""
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["LOG_FOLDER"] = str(tmp_path / "logs")
    env["LOG_LEVEL"] = "CRITICAL"
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, {"stdout": result.stdout, "stderr": result.stderr}
    payload = json.loads(result.stdout.strip().splitlines()[-1])

    assert not any(payload["loaded"].values())
    assert "pwa" in payload["blueprints"]
    assert "performance" not in payload["blueprints"]
    assert "president_scorecard_v2" not in payload["blueprints"]
    assert "workflow_dashboard_upgrade" not in payload["blueprints"]
    assert "bys360_pwa" not in payload["blueprints"]
    assert "main.workflow_president_approvals" not in payload["endpoints"]
    assert "president_scorecard_v2.president_approvals_tr_v2" not in payload["endpoints"]


def test_source_only_candidates_have_dependencies_that_block_safe_removal():
    """BYS360 P0 update: this test used to also assert that
    `app/templates/performance_v2_phase6_dashboard.html` contained
    `"main.workflow_executive_dashboard"` -- but that reference was itself a
    LIVE BUG, not a legitimate "blocks safe removal" dependency: the
    template is rendered by the genuinely ACTIVE `/performance/v2/faz6`
    route, and the referenced endpoint does not exist at runtime (`app.
    workflow.routes` is never imported at startup), so every real request
    to that page raised `werkzeug.routing.exceptions.BuildError` (a 500).
    See `tests/performance/test_phase6_dashboard_dead_workflow_link_fix.py`
    for the full fix evidence -- the dead button/link was removed from that
    template entirely. This test's remaining assertions (about the still-
    genuinely-source-only `app.workflow.routes`/scorecard-v2 candidates)
    were not affected by that fix and are unchanged below.
    """
    route_registry = (REPO_ROOT / "app" / "route_registry.py").read_text(encoding="utf-8")
    workflow_test = (
        REPO_ROOT / "tests" / "workflow" / "test_phase5w_workflow_schema_readiness.py"
    ).read_text(encoding="utf-8")
    scorecard_test = (
        REPO_ROOT / "tests" / "security" / "test_sql_identifier_escaping_negative.py"
    ).read_text(encoding="utf-8")
    scorecard_template = (
        REPO_ROOT / "app" / "templates" / "performance" / "president_approvals_v2.html"
    ).read_text(encoding="utf-8")
    openapi = (REPO_ROOT / "docs" / "api" / "openapi_draft.json").read_text(
        encoding="utf-8"
    )

    assert '"app.workflow.routes"' in route_registry
    assert "from app.workflow import routes" in workflow_test
    assert "from app.routes_president_scorecard_v2 import _qident" in scorecard_test
    assert "president_scorecard_v2.president_approval_scorecard_v2" in scorecard_template
    assert "main_bp_workflow_president_approvals" in openapi
    assert "president_scorecard_v2_bp_president_approvals_tr_v2" in openapi


def test_performance_v2_phase6_dashboard_no_longer_references_the_dead_workflow_endpoint():
    """Companion, positive-direction check for the P0 fix documented above:
    locks in that the dead reference stays gone."""
    workflow_template = (
        REPO_ROOT / "app" / "templates" / "performance_v2_phase6_dashboard.html"
    ).read_text(encoding="utf-8")
    assert "main.workflow_executive_dashboard" not in workflow_template
    assert "/workflow/executive-dashboard" not in workflow_template


def test_performance_blueprint_symbol_is_orphaned_but_package_is_live(app):
    from app import performance

    assert performance.performance_bp.name == "performance"
    assert not performance.performance_bp.deferred_functions
    assert "performance" not in app.blueprints
    assert "main" in app.blueprints
    assert any(
        rule.endpoint == "main.performance_president_approvals"
        for rule in app.url_map.iter_rules()
    )


def test_phase12a_route_and_conflict_totals_remain_unchanged(fresh_runtime_snapshot):
    runtime = fresh_runtime_snapshot["first"]
    assert runtime["counts"] == [985, 960, 880]
    conflicts = set(runtime["conflicts"])
    assert len(conflicts) == 9
    assert set(STRATEGIC_CONFLICTS) <= conflicts
    assert "/manifest.webmanifest" in conflicts
    assert "/performans/baskan-onaylari" in conflicts
