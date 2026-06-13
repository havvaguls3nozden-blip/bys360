
"""Communication export registry helpers.

Bu modül davranış üretmez; yalnızca ``app.communication.routes`` içindeki uyumluluk
re-export yüzeyini okunabilir ve denetlenebilir hale getirir.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import inspect
from typing import Any


_METADATA_PREFIXES = ("LEGACY_",)
_ALLOWED_NON_CALLABLE_EXPORTS = {
    "LEGACY_SHIM",
    "LEGACY_RUNTIME_STATUS",
    "LEGACY_ARCHIVE_MODULE",
    "LEGACY_ROUTE_FAMILY",
    "LEGACY_NOTE",
}


@dataclass(frozen=True)
class CommunicationExportEntry:
    name: str
    exists: bool
    kind: str
    module: str | None
    qualname: str | None

    def as_dict(self) -> dict[str, str | bool | None]:
        return {
            "name": self.name,
            "exists": self.exists,
            "kind": self.kind,
            "module": self.module,
            "qualname": self.qualname,
        }


def _entry_for(namespace: Mapping[str, Any], name: str) -> CommunicationExportEntry:
    marker = object()
    value = namespace.get(name, marker)
    if value is marker:
        return CommunicationExportEntry(
            name=name,
            exists=False,
            kind="missing",
            module=None,
            qualname=None,
        )

    if inspect.isfunction(value):
        kind = "function"
    elif callable(value):
        kind = "callable"
    elif name.startswith(_METADATA_PREFIXES) or name in _ALLOWED_NON_CALLABLE_EXPORTS:
        kind = "metadata"
    else:
        kind = type(value).__name__

    return CommunicationExportEntry(
        name=name,
        exists=True,
        kind=kind,
        module=getattr(value, "__module__", None),
        qualname=getattr(value, "__qualname__", None),
    )


def build_communication_export_registry(
    namespace: Mapping[str, Any],
    exported_names: Iterable[str],
) -> dict[str, dict[str, str | bool | None]]:
    """Build a serialisable registry for exported communication compatibility names."""

    return {
        name: _entry_for(namespace, name).as_dict()
        for name in exported_names
    }


def validate_communication_export_surface(
    namespace: Mapping[str, Any],
    exported_names: Iterable[str],
) -> dict[str, object]:
    """Validate the communication export surface without importing Flask internals.

    ``LEGACY_*`` entries are metadata and may be non-callable. Other names are expected
    to be callable route functions or aliases imported from domain route modules.
    """

    registry = build_communication_export_registry(namespace, exported_names)
    missing = [name for name, entry in registry.items() if not entry["exists"]]
    non_callable = [
        name
        for name, entry in registry.items()
        if name not in _ALLOWED_NON_CALLABLE_EXPORTS
        and not str(name).startswith(_METADATA_PREFIXES)
        and entry["exists"]
        and entry["kind"] not in {"function", "callable"}
    ]

    return {
        "ok": not missing and not non_callable,
        "export_count": len(registry),
        "missing": missing,
        "non_callable": non_callable,
        "registry": registry,
    }
