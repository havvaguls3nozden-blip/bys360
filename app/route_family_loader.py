
"""BYS360 route family loader helpers.

Faz 1B amacı: dağınık __init__ import bloklarını tek tip, okunabilir ve
raporlanabilir hale getirmek. Bu yardımcı modül, package içindeki route ailesi
modüllerini sıralı ve güvenli biçimde yükler.
"""
from __future__ import annotations

from collections.abc import Iterable
from importlib import import_module


def _normalize_module_name(module_name: str) -> str:
    module_name = (module_name or "").strip()
    if not module_name:
        raise ValueError("Boş modül adı yüklenemez.")
    return module_name if module_name.startswith(".") else f".{module_name}"


def load_required_modules(package_name: str, modules: Iterable[str]) -> list[str]:
    loaded: list[str] = []
    for module_name in modules:
        normalized = _normalize_module_name(module_name)
        import_module(normalized, package_name)
        loaded.append(normalized.lstrip("."))
    return loaded


def load_optional_modules(package_name: str, modules: Iterable[str]) -> tuple[list[str], list[str]]:
    loaded: list[str] = []
    failed: list[str] = []
    for module_name in modules:
        normalized = _normalize_module_name(module_name)
        try:
            import_module(normalized, package_name)
            loaded.append(normalized.lstrip("."))
        except Exception:
            failed.append(normalized.lstrip("."))
    return loaded, failed