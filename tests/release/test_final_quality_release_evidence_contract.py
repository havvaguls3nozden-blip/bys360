from __future__ import annotations

from pathlib import Path
from typing import cast

from app.refactor.final_quality_release_evidence_contract import (
    FINAL_RELEASE_EVIDENCE_CATEGORIES,
    FINAL_RELEASE_EVIDENCE_ITEMS,
    FINAL_RELEASE_FORBIDDEN_ACTIONS,
    get_final_quality_faz5_summary,
    get_release_evidence_category_keys,
    get_release_evidence_keys,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_release_evidence_manifest_has_required_core_items() -> None:
    keys = set(get_release_evidence_keys())
    required = {
        "core_refactor_final_lock",
        "scorecard_cleanup_lock",
        "home_phase1_lock",
        "final_quality_faz1_services",
        "final_quality_faz2_performance_rules",
        "final_quality_faz3_live_backbone",
        "final_quality_faz4_security_compliance",
        "clean_live_release_gate",
        "release_artifact_hygiene_gate",
    }
    assert required.issubset(keys)


def test_release_evidence_categories_cover_final_quality_dimensions() -> None:
    categories = set(get_release_evidence_category_keys())
    assert {
        "architecture",
        "service_tests",
        "performance_rules",
        "security_compliance",
        "release_hygiene",
        "home_experience",
    }.issubset(categories)


def test_release_evidence_items_have_markers_and_release_value() -> None:
    # BYS360 DEFECT FS (Final Sweep A3-16): `required_paths` is no longer
    # asserted non-empty here -- some items legitimately declare none now
    # (their prior paths never existed on disk; see
    # test_release_evidence_required_paths_actually_exist_on_disk below,
    # which is what actually enforces accuracy).
    assert len(FINAL_RELEASE_EVIDENCE_ITEMS) >= 9
    for item in FINAL_RELEASE_EVIDENCE_ITEMS:
        assert item.key
        assert item.title
        assert item.category
        assert item.command_markers
        assert item.release_value


def test_release_evidence_required_paths_actually_exist_on_disk() -> None:
    """BYS360 DEFECT FS (Final Sweep A3-16): this contract previously
    declared 15 of 20 required_paths across the 3 final_quality_*.py
    manifests that did not exist anywhere in the repository -- the tests
    only ever checked that `required_paths` was a non-empty tuple, never
    that any individual path resolved to a real file. Every path this
    contract currently declares must exist; a stale/never-built reference
    must be pruned from the manifest, not merely tolerated by the test."""
    missing: list[str] = []
    for item in FINAL_RELEASE_EVIDENCE_ITEMS:
        for path in item.required_paths:
            if not (REPO_ROOT / path).exists():
                missing.append(f"{item.key}: {path}")
    assert not missing, f"required_paths reference nonexistent files: {missing}"


def test_release_evidence_manifest_has_no_development_tool_trace() -> None:
    """BYS360 DEFECT FS (Final Sweep A3-15): keys and required_paths must
    not carry development-tool/agent naming traces (e.g. "claude")."""
    for item in FINAL_RELEASE_EVIDENCE_ITEMS:
        assert "claude" not in item.key.lower()
        for path in item.required_paths:
            assert "claude" not in path.lower()


def test_release_categories_reference_existing_manifest_keys() -> None:
    keys = set(get_release_evidence_keys())
    for category in FINAL_RELEASE_EVIDENCE_CATEGORIES:
        assert category.items
        assert category.required_marker
        assert set(category.items).issubset(keys)


def test_final_release_forbidden_actions_are_policy_labels_not_runtime_calls() -> None:
    joined = "\n".join(FINAL_RELEASE_FORBIDDEN_ACTIONS)
    assert "database schema mutation" in joined
    assert "external network call" in joined
    forbidden_runtime_tokens = [
        "db.session" + ".commit(",
        ".create" + "_all(",
        ".drop" + "_all(",
        "requests" + ".get(",
        "url" + "open(",
    ]
    for token in forbidden_runtime_tokens:
        assert token not in joined


def test_final_quality_faz5_summary_is_final_lock() -> None:
    summary = get_final_quality_faz5_summary()
    assert summary["runtime_mutation"] is False
    assert summary["database_migration"] is False
    assert summary["external_network"] is False
    assert summary["release_marker"] == "FINAL_QUALITY_FAZ5_CHAIN_OK"
    assert "FINAL_QUALITY_FAZ5_RELEASE_EVIDENCE_OK" in cast(tuple, summary["required_final_markers"])
