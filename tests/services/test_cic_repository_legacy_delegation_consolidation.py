from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from app.services import corporate_information_center
from app.services.cic import (
    access_policy,
    celebration_dates,
    cic_context,
    config_context,
    facade,
    misc_context,
    repository,
)

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_PATH = ROOT / "app/services/cic/repository.py"

CANONICAL_OWNERS = {
    "_cic_auto_last_run_key": cic_context,
    "_cic_phase3_actor_label": cic_context,
    "_cic_phase3_last_result": cic_context,
    "_cic_phase3_make_result": cic_context,
    "_cic_phase3_public_error": cic_context,
    "_cic_phase3_store_result": cic_context,
    "_cic_phase5_actor": cic_context,
    "_cic_phase5_now_label": cic_context,
    "_cic_phase5_store_audit": cic_context,
    "_cic_phase6_bool": cic_context,
    "_cic_v40_create_system_notifications": cic_context,
    "_cic_v40_date_input": cic_context,
    "_cic_v40_upcoming_special_days": cic_context,
    "_cic_v45_build_user_indexes": cic_context,
    "_cic_v45_ensure_schema": cic_context,
    "_cic_v45_existing_user_rows": cic_context,
    "_cic_phase5_audit_list": misc_context,
    "_cic_phase5_last_result": misc_context,
    "_cic_phase5_log_metrics": misc_context,
    "_cic_phase5_readiness": misc_context,
    "_cic_phase5_safe_int": misc_context,
    "_cic_phase6_build": misc_context,
    "_cic_phase6_log_quality": misc_context,
    "context": misc_context,
    "get_recent_logs": misc_context,
    "_cic_v40_setting_bool": celebration_dates,
    "_cic_v40_special_days": celebration_dates,
    "_cic_v40_special_days_today": celebration_dates,
    "_cic_v40_user_date": celebration_dates,
    "_clothing": config_context,
    "_tomorrow_note": config_context,
    "can_manage": access_policy,
}


def test_repository_no_longer_imports_or_calls_legacy_module() -> None:
    source = REPOSITORY_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert not any(
        isinstance(node, ast.ImportFrom)
        and node.module == "app.services"
        and any(
            alias.name == "corporate_information_center"
            for alias in node.names
        )
        for node in tree.body
    )
    assert not any(
        isinstance(node, ast.Import)
        and any(
            alias.name == "app.services.corporate_information_center"
            for alias in node.names
        )
        for node in tree.body
    )
    assert not any(
        isinstance(node, ast.Name) and node.id == "_legacy"
        for node in ast.walk(tree)
    )


def test_repository_legacy_names_resolve_to_canonical_owners() -> None:
    for name, owner in CANONICAL_OWNERS.items():
        expected = getattr(owner, name)
        assert getattr(repository, name) is expected, name
        assert getattr(facade, name) is expected, name


def test_legacy_entry_point_uses_canonical_access_policy() -> None:
    assert corporate_information_center.can_manage is access_policy.can_manage


def test_can_manage_policy_preserves_role_contract() -> None:
    assert not access_policy.can_manage(
        SimpleNamespace(is_authenticated=False, role="admin")
    )
    assert access_policy.can_manage(
        SimpleNamespace(is_authenticated=True, role="ADMIN")
    )
    assert access_policy.can_manage(
        SimpleNamespace(is_authenticated=True, role="sistem_yoneticisi")
    )
    assert not access_policy.can_manage(
        SimpleNamespace(is_authenticated=True, role="personel")
    )
    assert not access_policy.can_manage(
        SimpleNamespace(is_authenticated=True, role=None)
    )


def test_repository_is_removed_from_legacy_import_allowlist() -> None:
    guard_path = ROOT / "tests/architecture/test_cic_consolidation_guardrails_v1.py"
    source = guard_path.read_text(encoding="utf-8")
    assert '"app/services/cic/repository.py"' not in source
