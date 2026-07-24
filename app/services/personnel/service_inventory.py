from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .live_scope import PERSONNEL_SERVICE_MODULES


@dataclass(frozen=True, slots=True)
class PersonnelServiceFunction:
    module_key: str
    path: str
    name: str
    line: int
    is_private: bool
    category: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _categorise_function(name: str) -> str:
    lowered = name.lower()
    if lowered.startswith("build_"):
        return "context_builder"
    if lowered.startswith("validate_"):
        return "validation"
    if lowered.startswith("apply_"):
        return "mutation_mapper"
    if lowered.startswith("resolve_") or lowered.startswith("find_"):
        return "resolver"
    if "excel" in lowered:
        return "excel_import"
    if "leave" in lowered or "delegation" in lowered or "attendance" in lowered:
        return "leave_attendance_delegation"
    if lowered.startswith("_"):
        return "private_helper"
    return "service_helper"


def _scan_functions(path: Path, *, module_key: str, rel_path: str) -> list[PersonnelServiceFunction]:
    if not path.exists():
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except UnicodeDecodeError:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    functions: list[PersonnelServiceFunction] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                PersonnelServiceFunction(
                    module_key=module_key,
                    path=rel_path,
                    name=node.name,
                    line=int(getattr(node, "lineno", 0) or 0),
                    is_private=node.name.startswith("_"),
                    category=_categorise_function(node.name),
                )
            )
    return sorted(functions, key=lambda item: (item.path, item.line, item.name))


def build_personnel_service_inventory(project_root: str | Path = ".") -> dict[str, Any]:
    """Build an AST based inventory without importing application modules."""
    root = Path(project_root)
    functions: list[PersonnelServiceFunction] = []
    missing_modules: list[str] = []
    for item in PERSONNEL_SERVICE_MODULES:
        path = root / item.path
        if not path.exists():
            missing_modules.append(item.path)
            continue
        functions.extend(_scan_functions(path, module_key=item.key, rel_path=item.path))

    public_count = sum(1 for item in functions if not item.is_private)
    private_count = sum(1 for item in functions if item.is_private)
    categories: dict[str, int] = {}
    for func in functions:
        categories[func.category] = categories.get(func.category, 0) + 1

    return {
        "phase": "personnel_service_faz0",
        "module_count": len(PERSONNEL_SERVICE_MODULES),
        "missing_modules": missing_modules,
        "function_count": len(functions),
        "public_function_count": public_count,
        "private_function_count": private_count,
        "categories": dict(sorted(categories.items())),
        "functions": [item.to_dict() for item in functions],
    }


def render_personnel_service_inventory_markdown(project_root: str | Path = ".") -> str:
    inventory = build_personnel_service_inventory(project_root)
    lines = [
        "# Personel Yönetimi Servis Envanteri",
        "",
        f"- Modül sayısı: {inventory['module_count']}",
        f"- Fonksiyon sayısı: {inventory['function_count']}",
        f"- Public fonksiyon: {inventory['public_function_count']}",
        f"- Private/helper fonksiyon: {inventory['private_function_count']}",
        "",
        "## Kategori özeti",
    ]
    for key, count in inventory["categories"].items():
        lines.append(f"- `{key}`: {count}")
    if inventory["missing_modules"]:
        lines.extend(["", "## Eksik modüller"])
        lines.extend(f"- `{path}`" for path in inventory["missing_modules"])
    lines.extend(["", "## Fonksiyon yüzeyi"])
    for item in inventory["functions"]:
        visibility = "private" if item["is_private"] else "public"
        lines.append(f"- `{item['path']}:{item['line']}` — `{item['name']}` ({visibility}, {item['category']})")
    lines.append("")
    return "\n".join(lines)
