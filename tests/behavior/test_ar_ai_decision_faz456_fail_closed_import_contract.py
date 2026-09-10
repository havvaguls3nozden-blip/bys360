"""BYS360 DEFECT AR: app/ai/decision_support_faz{4,5,6}_routes.py each guard
their `from app.services.ai_decision.permission_guard import
assert_center_access, assert_evaluation_access` with a bare `try/except
Exception`. If that import ever fails for any reason (future circular
import, syntax error, transitive dependency issue), the except branch
previously defined LOCAL FALLBACK FUNCTIONS that unconditionally
``return True`` -- a fail-open: every AI Decision Support Faz 4/5/6 endpoint
(third-supervisor decisions, scorecard AI panels, low-performance
president-approval data) would become reachable by ANY authenticated user,
bypassing AIDecisionVisibilityScope-based scoping entirely, with only a
swallowed `logger.exception(...)` and no alert.

The fix replaces `return True` with `raise PermissionError(...)`: every
caller only uses these functions for their side effect (raising on denial),
never the return value, and each route file's own `_run_fazN_json` already
catches `PermissionError` and returns 403 -- so fail-closed is a drop-in
behavioral improvement with no other code path affected.

This is dormant code (the import currently succeeds in this codebase), so
it is tested by forcing the import to fail and reloading the module, then
proving the resulting fallback functions raise instead of returning True.
"""
from __future__ import annotations

import builtins
import importlib
import sys

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "app.ai.decision_support_faz4_routes",
        "app.ai.decision_support_faz5_routes",
        "app.ai.decision_support_faz6_routes",
    ],
)
def test_fallback_is_fail_closed_when_permission_guard_import_fails(module_name, monkeypatch):
    # Force `from app.services.ai_decision.permission_guard import ...` to
    # raise, exactly like a broken/circular import would, then reload the
    # route module so its module-level try/except re-runs and takes the
    # except branch. The route module uses a plain `from ... import ...`
    # statement, which goes through builtins.__import__ -- patch that
    # directly, since it's the actual mechanism Python uses.
    real_dunder_import = builtins.__import__

    def _blocked_dunder_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "app.services.ai_decision.permission_guard":
            raise ImportError("BYS360-AR-SIMULATED-PERMISSION-GUARD-IMPORT-FAILURE")
        return real_dunder_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _blocked_dunder_import)

    if module_name in sys.modules:
        module = importlib.reload(sys.modules[module_name])
    else:
        module = importlib.import_module(module_name)

    try:
        # Before the fix: these would return True (fail-open). After the
        # fix: they must raise PermissionError (fail-closed).
        with pytest.raises(PermissionError):
            module.assert_center_access(user=None)
        with pytest.raises(PermissionError):
            module.assert_evaluation_access(user=None, evaluation=None)
    finally:
        # Restore the module to its real (import-succeeding) state so it
        # doesn't leak the fail-open-free-but-import-broken stub into any
        # later test in the same process.
        monkeypatch.undo()
        importlib.reload(sys.modules[module_name])
