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
it is tested by forcing the import to fail and proving the resulting
fallback functions raise instead of returning True.

BYS360 DEFECT AR (test-methodology repair): the original version of this
test forced the failure via `importlib.reload()` on the route module INSIDE
the parent pytest process. That re-executes the module's top-level
`@main_bp.route(...)` decorators -- which works when this file runs alone
(nothing has created a Flask app yet, so the shared `main` blueprint is
still open for registration), but fails deterministically inside the full
canonical suite once ANY earlier test has called `create_app()`: Flask
permanently locks a blueprint after its first registration, and raises
`AssertionError: The setup method 'route' can no longer be called on the
blueprint 'main'...` on the reload's re-decoration attempt. That failure is
a flaw in this test's technique, not in the production fail-closed fix
(confirmed: the same 3 checks passed cleanly whenever this file ran in
isolation, and the failure position was 100% deterministic and tied to
suite composition, not to the fix itself).

The repair moves the sensitive import-and-decorate step into a FRESH
Python subprocess per module, so the shared parent-process Flask blueprint
state is never touched. Each subprocess blocks only the one exact
permission-guard import at the `builtins.__import__` level, imports the
target route module for the very first time in that process, and calls the
same fallback functions the original test called -- genuine behavioral
execution, not source/AST inspection.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

_BLOCKED_IMPORT = "app.services.ai_decision.permission_guard"

# Runs in a brand-new interpreter (no pytest, no Flask app, no other test's
# import/blueprint state). Blocks only the one exact dependency import,
# imports the target route module for the first time, and behaviorally
# proves both fallback functions raise PermissionError instead of
# returning True.
_CHILD_SCRIPT = """
import builtins
import importlib
import sys

_BLOCKED = {blocked!r}
_real_import = builtins.__import__


def _blocked_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == _BLOCKED:
        raise ImportError("BYS360-AR-SIMULATED-PERMISSION-GUARD-IMPORT-FAILURE")
    return _real_import(name, globals, locals, fromlist, level)


builtins.__import__ = _blocked_import

module = importlib.import_module({module_name!r})

errors = []

try:
    module.assert_center_access(user=None)
    errors.append("assert_center_access(user=None) did not raise")
except PermissionError:
    pass
except Exception as exc:
    errors.append(f"assert_center_access raised {{type(exc).__name__}}, not PermissionError: {{exc}}")

try:
    module.assert_evaluation_access(user=None, evaluation=None)
    errors.append("assert_evaluation_access(user=None, evaluation=None) did not raise")
except PermissionError:
    pass
except Exception as exc:
    errors.append(f"assert_evaluation_access raised {{type(exc).__name__}}, not PermissionError: {{exc}}")

if errors:
    print("BYS360_AR_CHILD_FAIL: " + "; ".join(errors))
    sys.exit(1)

print("BYS360_AR_CHILD_OK")
sys.exit(0)
"""


@pytest.mark.parametrize(
    "module_name",
    [
        "app.ai.decision_support_faz4_routes",
        "app.ai.decision_support_faz5_routes",
        "app.ai.decision_support_faz6_routes",
    ],
)
def test_fallback_is_fail_closed_when_permission_guard_import_fails(module_name):
    script = _CHILD_SCRIPT.format(blocked=_BLOCKED_IMPORT, module_name=module_name)
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0 and "BYS360_AR_CHILD_OK" in result.stdout, (
        f"Fresh-subprocess fail-closed check failed for {module_name}\n"
        f"returncode={result.returncode}\n"
        f"stdout={result.stdout}\n"
        f"stderr={result.stderr}"
    )
