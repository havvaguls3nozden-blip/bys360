from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PUBLIC_SERVICE_MODULES = {
    "app.services.cic.facade",
    "app.services.cic.service",
}

PUBLIC_OPERATIONS = {
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
}

ROUTE_CONTRACT = {
    ("GET", "/dashboard/kurumsal-bilgilendirme"),
    ("GET", "/dashboard/kurumsal-bilgilendirme/gorevler"),
    ("POST", "/dashboard/kurumsal-bilgilendirme/gorevler"),
    ("GET", "/dashboard/kurumsal-bilgilendirme/alicilar"),
    ("POST", "/dashboard/kurumsal-bilgilendirme/alicilar"),
    ("GET", "/dashboard/kurumsal-bilgilendirme/sablonlar"),
    ("POST", "/dashboard/kurumsal-bilgilendirme/sablonlar"),
    ("GET", "/dashboard/kurumsal-bilgilendirme/test"),
    ("POST", "/dashboard/kurumsal-bilgilendirme/test"),
    (
        "POST",
        "/dashboard/kurumsal-bilgilendirme/gorevler/<task_key>/calistir",
    ),
    ("GET", "/dashboard/kurumsal-bilgilendirme/loglar"),
    ("GET", "/dashboard/kurumsal-bilgilendirme/sistem"),
    ("POST", "/dashboard/kurumsal-bilgilendirme/sistem"),
    ("GET", "/dashboard/kurumsal-bilgilendirme/kutlamalar"),
    ("POST", "/dashboard/kurumsal-bilgilendirme/kutlamalar"),
    (
        "POST",
        "/dashboard/kurumsal-bilgilendirme/kutlamalar/<task_key>/calistir",
    ),
    (
        "GET",
        "/dashboard/kurumsal-bilgilendirme/kutlamalar/excel-sablon",
    ),
    (
        "POST",
        "/dashboard/kurumsal-bilgilendirme/kutlamalar/excel-yukle",
    ),
}

TASK_KEYS = {
    "manager_evening",
    "manager_morning",
    "special_day",
    "staff_birthday",
    "staff_evening",
    "staff_morning",
    "staff_noon",
    "work_anniversary",
}

LEGACY_IMPORT_ALLOWLIST = {
    "app/services/cic/celebration_service.py",
    "app/services/cic/mail_scheduler_service.py",
    "app/services/cic/query_service.py",
    "app/services/cic/repository.py",
    "app/services/cic/template_service.py",
    "scripts/communication/run_corporate_information_task.py",
}

ENGINE_IMPORT_ALLOWLIST = {
    "scripts/communication/run_corporate_information_center_task_v3_0_phase2.py",
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


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


def _imported_names_from_public_modules() -> set[str]:
    imported: set[str] = set()
    for path in _active_python_files():
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith("app/services/cic/"):
            continue
        for node in ast.walk(_parse(path)):
            if isinstance(node, ast.ImportFrom) and node.module in PUBLIC_SERVICE_MODULES:
                imported.update(alias.name for alias in node.names)
    return imported


def _legacy_importers(module_name: str) -> set[str]:
    importers: set[str] = set()
    module_tail = module_name.rsplit(".", 1)[-1]
    module_parent = module_name.rsplit(".", 1)[0]

    for path in _active_python_files():
        relative = path.relative_to(ROOT).as_posix()
        for node in ast.walk(_parse(path)):
            if isinstance(node, ast.ImportFrom):
                direct_match = node.module == module_name
                parent_match = (
                    node.module == module_parent
                    and any(alias.name == module_tail for alias in node.names)
                )
                if direct_match or parent_match:
                    importers.add(relative)
            elif isinstance(node, ast.Import):
                if any(alias.name == module_name for alias in node.names):
                    importers.add(relative)
    return importers


def _route_contract() -> set[tuple[str, str]]:
    path = ROOT / "app/communication/corporate_information_center_routes.py"
    routes: set[tuple[str, str]] = set()
    for node in _parse(path).body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            function = decorator.func
            if not (
                isinstance(function, ast.Attribute)
                and isinstance(function.value, ast.Name)
                and function.value.id == "main_bp"
                and function.attr in {"get", "post"}
                and decorator.args
                and isinstance(decorator.args[0], ast.Constant)
                and isinstance(decorator.args[0].value, str)
            ):
                continue
            routes.add((function.attr.upper(), decorator.args[0].value))
    return routes


def test_cic_external_public_operation_surface_is_stable() -> None:
    assert _imported_names_from_public_modules() == PUBLIC_OPERATIONS


def test_cic_route_contract_is_stable() -> None:
    assert _route_contract() == ROUTE_CONTRACT


def test_cic_task_contract_is_stable() -> None:
    from app.services.cic.task_contract import task_keys

    assert set(task_keys()) == TASK_KEYS


def test_cic_legacy_import_allowlists_can_only_shrink() -> None:
    legacy_importers = _legacy_importers(
        "app.services.corporate_information_center"
    )
    engine_importers = _legacy_importers(
        "app.services.corporate_information_center_engine"
    )

    assert legacy_importers <= LEGACY_IMPORT_ALLOWLIST
    assert engine_importers <= ENGINE_IMPORT_ALLOWLIST


def test_cic_external_consumers_do_not_import_private_service_names() -> None:
    private_imports = {
        name
        for name in _imported_names_from_public_modules()
        if name.startswith("_")
    }
    assert private_imports == set()
