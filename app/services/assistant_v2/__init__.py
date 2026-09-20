"""BYS360 Assistant V2 -- module/data/capability architecture (first slice).

This package is the first real code slice of BYS360 Assistant V2. It holds:

  - `capability_registry`: the additive, read-only registry of what the
    assistant can DO, per module (mirrors
    `app.services.settings.module_registry`'s established pattern).
  - `read_adapters`: thin, bounded, non-authorizing read functions for the
    capabilities that had no pre-existing narrow-enough service function to
    reuse.

No route, blueprint, or UI is registered by this package yet -- that is a
later, separately-reviewed phase.
"""
from __future__ import annotations

from .capability_registry import (
    ASSISTANT_CAPABILITY_REGISTRY,
    AssistantCapabilityEntry,
    find_capabilities_missing_permission,
    find_capabilities_with_invalid_operation_type,
    find_capabilities_with_orphan_module_key,
    find_capabilities_with_unresolvable_service,
    find_duplicate_capability_keys,
    get_capability,
    get_capability_registry,
    list_active_capabilities,
    list_capabilities_for_module,
)

__all__ = [
    "AssistantCapabilityEntry",
    "ASSISTANT_CAPABILITY_REGISTRY",
    "get_capability_registry",
    "get_capability",
    "list_capabilities_for_module",
    "list_active_capabilities",
    "find_duplicate_capability_keys",
    "find_capabilities_missing_permission",
    "find_capabilities_with_orphan_module_key",
    "find_capabilities_with_unresolvable_service",
    "find_capabilities_with_invalid_operation_type",
]
