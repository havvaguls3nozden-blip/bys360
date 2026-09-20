"""BYS360 Assistant V2 -- capability registry completeness contract.

Proves the invariants `app.services.assistant_v2.capability_registry` exists
to guarantee, mirroring the exact house style established by
`tests/quality/test_settings_center_v2_completeness_contract_v1.py`:

  - no duplicate capability_key entered the registry;
  - every capability has a real authorization path -- either a real
    permission_key, or is explicitly self-describing, or documents one of
    the three reviewed `auth_override` exceptions (never silently ungated);
  - every capability's module_key actually exists in the independently
    maintained `app.services.settings.module_registry.MODULE_REGISTRY`
    (no orphan module reference);
  - every capability's service_handler dotted path actually imports to a
    real, callable function in this worktree (no speculative/stale path);
  - every capability's operation_type is one of the declared OPERATION_TYPES;
  - every capability is read-only for this V2 slice (deliberately temporary
    -- see the test's own docstring below);
  - every active module in MODULE_REGISTRY is covered by at least one
    capability;
  - the module-count and capability-count are pinned, so a silent drop (or
    a silent, unreviewed addition) is caught by CI.

This file does NOT stand up a Flask app or touch any database -- every test
here is a pure, in-memory check over the two plain-Python registries, so it
runs everywhere `test_settings_center_v2_completeness_contract_v1.py`'s own
"A: pure-registry contracts" section does.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.ci_safe


def test_no_duplicate_capability_keys() -> None:
    from app.services.assistant_v2.capability_registry import find_duplicate_capability_keys

    assert find_duplicate_capability_keys() == []


def test_no_capability_missing_permission() -> None:
    """Every capability must have a real, enforceable authorization path --
    a real permission_key, OR is_self_describing=True, OR a documented
    extra['auth_override']. A capability with none of the three would be
    silently ungated, which this project's own mandate explicitly forbids."""
    from app.services.assistant_v2.capability_registry import find_capabilities_missing_permission

    assert find_capabilities_missing_permission() == []


def test_no_capability_with_orphan_module_key() -> None:
    """Every capability's module_key must exist in the real,
    independently-maintained app.services.settings.module_registry.MODULE_REGISTRY
    -- this registry is additive on top of that one, never a source of new,
    invented module names."""
    from app.services.assistant_v2.capability_registry import (
        find_capabilities_with_orphan_module_key,
    )

    assert find_capabilities_with_orphan_module_key() == []


def test_no_capability_with_unresolvable_service() -> None:
    """Every capability's service_handler dotted path must actually import
    to a real, callable function in this worktree -- no speculative or
    stale path is allowed to reach the registry."""
    from app.services.assistant_v2.capability_registry import (
        find_capabilities_with_unresolvable_service,
    )

    assert find_capabilities_with_unresolvable_service() == []


def test_no_capability_with_invalid_operation_type() -> None:
    from app.services.assistant_v2.capability_registry import (
        find_capabilities_with_invalid_operation_type,
    )

    assert find_capabilities_with_invalid_operation_type() == []


def test_all_capabilities_are_read_only_for_v2() -> None:
    """V2 read-first mandate: every capability registered in this slice must
    be read_or_write='read'. This is DELIBERATELY TEMPORARY -- write
    capabilities (CREATE/UPDATE/APPROVE/DELETE/EXPORT) are explicitly out of
    scope for this slice and may only be introduced in a later, separately
    reviewed phase that adds its own authorization/audit story for writes.
    This test should be relaxed (e.g. to assert a specific allow-list of
    write capabilities) only as part of that deliberate future phase, never
    incidentally."""
    from app.services.assistant_v2.capability_registry import ASSISTANT_CAPABILITY_REGISTRY

    non_read = [e.capability_key for e in ASSISTANT_CAPABILITY_REGISTRY if e.read_or_write != "read"]
    assert non_read == [], f"V2 is read-only; found non-read capabilities: {non_read}"


def test_every_active_module_has_at_least_one_capability() -> None:
    """Cross-references against the real, independently-maintained module
    registry: every active module must be covered by at least one
    capability. Reports the exact module_keys with zero coverage (if any)
    rather than a bare count, so a gap is immediately actionable."""
    from app.services.assistant_v2.capability_registry import ASSISTANT_CAPABILITY_REGISTRY
    from app.services.settings.module_registry import get_module_registry

    covered_module_keys = {e.module_key for e in ASSISTANT_CAPABILITY_REGISTRY}
    active_module_keys = {m.module_key for m in get_module_registry() if m.active}
    missing = sorted(active_module_keys - covered_module_keys)
    assert missing == [], f"active modules with zero assistant_v2 capabilities: {missing}"


def test_capability_registry_module_count_matches_expected() -> None:
    """Pins the exact number of distinct module_keys this slice's capability
    registry covers. This intentionally mirrors every one of the 16 active
    modules in app.services.settings.module_registry.MODULE_REGISTRY (see
    test_registry_covers_the_discovered_real_modules in the sibling Settings
    Center V2 completeness contract for that same set of 16 module_keys).
    A change to this number means a module was added or removed from
    coverage and must be a deliberate, reviewed change, not an accident."""
    from app.services.assistant_v2.capability_registry import ASSISTANT_CAPABILITY_REGISTRY

    module_keys = {e.module_key for e in ASSISTANT_CAPABILITY_REGISTRY}
    assert len(module_keys) == 16, f"expected exactly 16 covered module_keys, found {len(module_keys)}: {sorted(module_keys)}"


def test_capability_count_is_pinned() -> None:
    """Pins the exact total capability count for this slice. The initial
    design target was 48 (16 modules x 3 capabilities each); a coordinator
    review then deliberately trimmed security_session from 3 capabilities to
    1 (system_critical module, no route_endpoint -- even a lockout-listing
    capability was judged a reconnaissance risk), landing at 46. A later
    wave added performance_mgmt_list_incomplete_evaluations (47) to support
    the Phase G cross-module orchestration worked example (personnel +
    performance intersection) with a real, evidence-grounded capability
    rather than a fake/demo one. The legacy-migration wave added
    virtual_assistant_search_knowledge_bank (48), wrapping the existing
    admin-teachable knowledge bank rather than a hardcoded dictionary. The
    same wave added performance_mgmt_summarize_kpi_targets (49) after Phase
    G's mechanical ownership research established performance_mgmt (not
    "dashboard", despite the source bridge file's name) as the real owner,
    reusing dashboard_kpi_bridge.py's existing computation rather than
    duplicating it. Any future change to this number (adding/removing a
    capability) must update this pin deliberately -- a silent drift here
    would mean the registry changed without review."""
    from app.services.assistant_v2.capability_registry import ASSISTANT_CAPABILITY_REGISTRY

    assert len(ASSISTANT_CAPABILITY_REGISTRY) == 49, (
        f"expected exactly 49 capabilities, found {len(ASSISTANT_CAPABILITY_REGISTRY)}"
    )
