from __future__ import annotations

import ast
from pathlib import Path

import app.services.cic as cic_package
from app.services.cic import (
    access_policy,
    celebration_service,
    config_context,
    mail_service,
    misc_context,
    save_context,
    scheduler_service,
    service,
    template_service,
)

ROOT = Path(__file__).resolve().parents[2]
SERVICE_MODULE = "app.services.cic.service"
FACADE_MODULE = "app.services.cic.facade"

EXPECTED_SERVICE_EXPORTS = (
    "can_manage",
    "celebration_context",
    "context",
    "ensure_celebration_schema",
    "ensure_defaults",
    "import_celebration_dates_from_excel",
    "run_due_tasks",
    "save_celebration_settings",
    "save_recipients",
    "save_system",
    "save_tasks",
    "save_templates",
    "send_task",
)

EXPECTED_CONSUMERS = {
    "app/communication/corporate_information_center_routes.py": {
        "can_manage",
        "celebration_context",
        "context",
        "ensure_celebration_schema",
        "ensure_defaults",
        "import_celebration_dates_from_excel",
        "save_celebration_settings",
        "save_recipients",
        "save_system",
        "save_tasks",
        "save_templates",
        "send_task",
    },
    "scripts/scheduled/run_cic_auto_scheduler.py": {"run_due_tasks"},
}

CANONICAL_OWNERS = {
    "can_manage": access_policy,
    "celebration_context": celebration_service,
    "context": misc_context,
    "ensure_celebration_schema": celebration_service,
    "ensure_defaults": config_context,
    "import_celebration_dates_from_excel": celebration_service,
    "run_due_tasks": scheduler_service,
    "save_celebration_settings": celebration_service,
    "save_recipients": save_context,
    "save_system": save_context,
    "save_tasks": save_context,
    "save_templates": template_service,
    "send_task": mail_service,
}


def _active_python_files() -> list[Path]:
    files: list[Path] = []
    for base in (ROOT / "app", ROOT / "scripts"):
        for path in base.rglob("*.py"):
            relative = path.relative_to(ROOT).as_posix()
            if relative.startswith("scripts/archive/"):
                continue
            files.append(path)
    return sorted(files)


def _public_imports(module_name: str) -> dict[str, set[str]]:
    imports: dict[str, set[str]] = {}
    for path in _active_python_files():
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith("app/services/cic/"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == module_name:
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Import) and any(
                alias.name == module_name for alias in node.names
            ):
                names.add("<module>")
        if names:
            imports[relative] = names
    return imports


def test_cic_service_export_contract_is_exact_and_public_only() -> None:
    assert tuple(service.__all__) == EXPECTED_SERVICE_EXPORTS
    assert len(set(service.__all__)) == len(EXPECTED_SERVICE_EXPORTS)
    assert all(not name.startswith("_") for name in service.__all__)
    assert all(hasattr(service, name) for name in service.__all__)


def test_cic_service_exports_resolve_to_canonical_owners() -> None:
    for name, owner in CANONICAL_OWNERS.items():
        assert getattr(service, name) is getattr(owner, name), name


def test_cic_package_exposes_canonical_service_entrypoint() -> None:
    assert cic_package.service is service
    assert "service" in cic_package.__all__


def test_active_consumers_use_only_the_canonical_service_entrypoint() -> None:
    assert _public_imports(SERVICE_MODULE) == EXPECTED_CONSUMERS
    assert _public_imports(FACADE_MODULE) == {}


def test_cic_service_consumer_union_matches_public_contract() -> None:
    imported = set().union(*EXPECTED_CONSUMERS.values())
    assert imported == set(EXPECTED_SERVICE_EXPORTS)
