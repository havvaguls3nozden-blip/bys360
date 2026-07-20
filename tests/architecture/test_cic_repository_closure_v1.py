from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import app.services.cic as cic_package
from app.services.cic import (
    access_policy,
    celebration_dates,
    cic_context,
    config_context,
    facade,
    misc_context,
)

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_MODULE = "app.services.cic.repository"
REPOSITORY_PATH = ROOT / "app/services/cic/repository.py"

EXPECTED_FACADE_EXPORTS = (
    "BASE_KEY",
    "TASK_DEFINITIONS",
    "_active_staff_users",
    "_cic_auto_bool",
    "_cic_auto_last_run_key",
    "_cic_is_weekend",
    "_cic_phase3_actor_label",
    "_cic_phase3_last_result",
    "_cic_phase3_make_result",
    "_cic_phase3_public_error",
    "_cic_phase3_store_result",
    "_cic_phase3_task_label",
    "_cic_phase5_actor",
    "_cic_phase5_audit_list",
    "_cic_phase5_last_result",
    "_cic_phase5_log_metrics",
    "_cic_phase5_mail_health",
    "_cic_phase5_now_label",
    "_cic_phase5_readiness",
    "_cic_phase5_safe_int",
    "_cic_phase5_store_audit",
    "_cic_phase5_task_preview",
    "_cic_phase6_bool",
    "_cic_phase6_build",
    "_cic_phase6_item",
    "_cic_phase6_log_quality",
    "_cic_phase6_missing_email_count",
    "_cic_phase6_status",
    "_cic_phase6_template_quality",
    "_cic_v11_bool",
    "_cic_v11_clean_header",
    "_cic_v11_get_setting_value",
    "_cic_v11_mail_settings",
    "_cic_v11_normalize_email",
    "_cic_v11_send_email_direct",
    "_cic_v40_active_staff_candidates",
    "_cic_v40_anniversary_users",
    "_cic_v40_birthday_users",
    "_cic_v40_bool",
    "_cic_v40_create_system_notifications",
    "_cic_v40_date_input",
    "_cic_v40_days_until",
    "_cic_v40_mmdd",
    "_cic_v40_parse_date",
    "_cic_v40_run_weekend_celebrations",
    "_cic_v40_service_year",
    "_cic_v40_setting_bool",
    "_cic_v40_special_day_users",
    "_cic_v40_special_days",
    "_cic_v40_special_days_today",
    "_cic_v40_today",
    "_cic_v40_upcoming_special_days",
    "_cic_v40_upcoming_users",
    "_cic_v40_user_date",
    "_cic_v45_bool",
    "_cic_v45_build_user_indexes",
    "_cic_v45_ensure_schema",
    "_cic_v45_existing_user_rows",
    "_cic_v45_header_key",
    "_cic_v45_norm",
    "_cic_v45_norm_name",
    "_cic_v45_parse_date",
    "_cic_v45_text",
    "_cic_weekday_name_tr",
    "_clean_ids",
    "_clothing",
    "_dashboard_counts",
    "_dumps_json",
    "_format_weather",
    "_has_settings_table",
    "_loads_json",
    "_now",
    "_recipients_for_task",
    "_render_template_text",
    "_tomorrow_note",
    "_user_name",
    "_users_by_ids",
    "_weather",
    "can_manage",
    "celebration_context",
    "context",
    "ensure_celebration_schema",
    "ensure_defaults",
    "get_auto_scheduler_config",
    "get_config",
    "get_recent_logs",
    "get_recipients",
    "get_setting",
    "get_template",
    "import_celebration_dates_from_excel",
    "list_users",
    "run_due_tasks",
    "save_celebration_settings",
    "save_recipients",
    "save_system",
    "save_tasks",
    "save_templates",
    "send_task",
    "set_auto_scheduler_config",
    "set_setting",
)

FORMER_REPOSITORY_OWNERS = {
    "_cic_auto_bool": misc_context,
    "_cic_auto_last_run_key": cic_context,
    "_cic_is_weekend": cic_context,
    "_cic_phase3_actor_label": cic_context,
    "_cic_phase3_last_result": cic_context,
    "_cic_phase3_make_result": cic_context,
    "_cic_phase3_public_error": cic_context,
    "_cic_phase3_store_result": cic_context,
    "_cic_phase5_actor": cic_context,
    "_cic_phase5_audit_list": misc_context,
    "_cic_phase5_last_result": misc_context,
    "_cic_phase5_log_metrics": misc_context,
    "_cic_phase5_now_label": cic_context,
    "_cic_phase5_readiness": misc_context,
    "_cic_phase5_safe_int": misc_context,
    "_cic_phase5_store_audit": cic_context,
    "_cic_phase6_bool": cic_context,
    "_cic_phase6_build": misc_context,
    "_cic_phase6_log_quality": misc_context,
    "_cic_v40_bool": celebration_dates,
    "_cic_v40_create_system_notifications": cic_context,
    "_cic_v40_date_input": cic_context,
    "_cic_v40_days_until": celebration_dates,
    "_cic_v40_mmdd": celebration_dates,
    "_cic_v40_parse_date": celebration_dates,
    "_cic_v40_setting_bool": celebration_dates,
    "_cic_v40_special_days": celebration_dates,
    "_cic_v40_special_days_today": celebration_dates,
    "_cic_v40_today": celebration_dates,
    "_cic_v40_upcoming_special_days": cic_context,
    "_cic_v40_user_date": celebration_dates,
    "_cic_v45_bool": cic_context,
    "_cic_v45_build_user_indexes": cic_context,
    "_cic_v45_ensure_schema": cic_context,
    "_cic_v45_existing_user_rows": cic_context,
    "_cic_v45_header_key": cic_context,
    "_cic_v45_norm": cic_context,
    "_cic_v45_norm_name": cic_context,
    "_cic_v45_parse_date": cic_context,
    "_cic_v45_text": cic_context,
    "_cic_weekday_name_tr": cic_context,
    "_clean_ids": config_context,
    "_clothing": config_context,
    "_dumps_json": config_context,
    "_has_settings_table": config_context,
    "_loads_json": config_context,
    "_now": config_context,
    "_tomorrow_note": config_context,
    "can_manage": access_policy,
    "context": misc_context,
    "get_recent_logs": misc_context,
}


def _active_python_files() -> list[Path]:
    paths = []
    for base in (ROOT / "app", ROOT / "scripts", ROOT / "tests"):
        for path in base.rglob("*.py"):
            relative = path.relative_to(ROOT).as_posix()
            if relative.startswith("scripts/archive/"):
                continue
            paths.append(path)
    return sorted(paths)


def _imports_repository(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == REPOSITORY_MODULE:
                return True
            if node.module == "app.services.cic" and any(
                alias.name == "repository" for alias in node.names
            ):
                return True
            relative = path.relative_to(ROOT).as_posix()
            in_cic_package = relative.startswith("app/services/cic/")
            if in_cic_package and node.level and node.module == "repository":
                return True
            if (
                in_cic_package
                and node.level
                and node.module is None
                and any(alias.name == "repository" for alias in node.names)
            ):
                return True
        elif isinstance(node, ast.Import) and any(
            alias.name == REPOSITORY_MODULE for alias in node.names
        ):
            return True
    return False


def test_repository_module_is_deleted_and_not_package_exported() -> None:
    assert not REPOSITORY_PATH.exists()
    assert importlib.util.find_spec(REPOSITORY_MODULE) is None
    assert not hasattr(cic_package, "repository")
    assert "repository" not in cic_package.__all__


def test_active_code_has_no_repository_imports() -> None:
    offenders = [
        path.relative_to(ROOT).as_posix()
        for path in _active_python_files()
        if _imports_repository(path)
    ]
    assert offenders == []


def test_facade_export_contract_is_exactly_preserved() -> None:
    assert tuple(facade.__all__) == EXPECTED_FACADE_EXPORTS
    assert all(hasattr(facade, name) for name in EXPECTED_FACADE_EXPORTS)


def test_former_repository_names_resolve_directly_to_canonical_owners() -> None:
    for name, owner in FORMER_REPOSITORY_OWNERS.items():
        assert getattr(facade, name) is getattr(owner, name), name


def test_facade_source_has_no_repository_bridge_import() -> None:
    facade_path = ROOT / "app/services/cic/facade.py"
    assert not _imports_repository(facade_path)
