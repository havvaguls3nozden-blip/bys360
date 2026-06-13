"""BYS360 Core Refactor Faz 8 alias wrapper.

Bu modül, eski faz numaralı route dosyasını silmeden anlamlı bir import yolu
sağlar. Runtime kayıt akışı eski dosyayı kullanmaya devam eder; bu wrapper
ancak yeni kod açıkça bu anlamlı modül adını import ederse devreye girer.
"""
from __future__ import annotations


from importlib import import_module
from types import ModuleType
from typing import Any

ALIAS_WRAPPER_VERSION = "2026-04-21-core-refactor-faz8-lazy-wrapper"
ALIAS_FOR = "app.institutional.hr_personnel_phase12_routes"
LEGACY_MODULE = ALIAS_FOR
RUNTIME_RENAME_ALLOWED = False


def _legacy_module() -> ModuleType:
    """Legacy faz modülünü talep anında yükler."""

    return import_module(LEGACY_MODULE)


def __getattr__(name: str) -> Any:
    """Alias modülde bulunmayan özniteliği legacy modülden verir."""

    return getattr(_legacy_module(), name)


def __dir__() -> list[str]:
    """Geliştirici araçlarında legacy öznitelikleri de görünür kılar."""

    return sorted(set(globals()) | set(dir(_legacy_module())))
