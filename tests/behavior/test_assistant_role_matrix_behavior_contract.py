"""Pre-consolidation behavior contract for TD-CAND-002 (duplicate,
independently-drifting assistant-role-matrix subsystem):

  - app/main_handlers/account_settings_helpers.py (BYS360_ASSISTANT_ROLE_MATRIX_V12_FIX
    block, lines 852-1094) -- "settings" implementation. This is the only one of the two
    with a confirmed live caller: settings_page() (account_settings_helpers.py:192,486,498),
    routed via /settings.
  - app/main_handlers/account_communication_helpers.py (BYS360_ASSISTANT_ROLE_MATRIX_SETTINGS_V11
    block, lines 581-748) -- "communication" implementation. Forensic search this wave
    (grep for every import of _build_assistant_role_matrix / save_assistant_role_matrix_from_form
    / reset_assistant_role_matrix_defaults across app/) found no live caller: it is imported
    and re-exported by account_visibility_helpers.py's __all__, but nothing imports those three
    specific names from there either. Tested here anyway, directly, so its current contract is
    still locked before any future consolidation touches it.

This file does NOT fix, unify, or normalize the two implementations. It documents and locks
CURRENT behavior only, per the TD-CAND-002 behavior-locking wave. Where the two implementations
differ, both sides get their own explicitly-named test asserting their own current output --
neither side is treated as "correct".

Key forensic correction to the registry's original framing: the literal null-guard line in the
communication implementation ("if not visible_roles: visible_roles = set()") is inert dead code
in the CURRENT implementation -- _assistant_visible_roles_from_settings() already always returns
a set (never None), so the guard never actually fires. The real, verified divergence is in how
each implementation's OWN _assistant_visible_roles_from_settings() falls back when the raw
"visible_roles" string it reads is empty (not the same as an exception being raised while
reading it -- both implementations agree on that case, see the exception-path tests below):
  - settings:      empty raw string -> falls back to the 7 ASSISTANT_DEFAULT_VISIBLE_ROLES
  - communication:  empty raw string -> stays an empty set (no fallback)

Separately: app/services/assistant_settings_service.py::get_assistant_settings() (the shared
data source both implementations call) has ITS OWN independent defaulting layer that currently
never actually hands back an empty "visible_roles" string in practice (see
test_*_visible_roles_on_fresh_unconfigured_db_returns_default_seven below) -- so today, with
the real service, both implementations currently converge on the same 7-role default for a
never-configured install. The two implementations' own divergent fallback logic is real code,
correctly locked here via a mocked get_assistant_settings(), but is not currently observable
end-to-end through the live service. A future change to get_assistant_settings() that starts
returning a genuinely empty "visible_roles" string would make this divergence immediately
observable in production -- these tests exist precisely so that day is caught, not surprised by.
"""
from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import pytest

_TEST_DB_ROOT = Path(tempfile.gettempdir()) / "bys360" / "role_matrix_behavior_tmp" / "test_dbs"


def _make_app(monkeypatch, **env_overrides):
    """Per-test, file-backed SQLite app -- same proven isolation pattern already used by
    tests/behavior/test_settings_page_behavior_contract.py and ~24 other test files in this
    suite (see each file's own _make_app), deliberately not the shared session-scoped
    app/client fixtures in tests/conftest.py: these tests need to control the exact set of
    ModuleSetting rows present (including "zero rows at all"), which a DB shared with other
    tests running in the same session cannot guarantee."""
    _TEST_DB_ROOT.mkdir(parents=True, exist_ok=True)
    db_path = _TEST_DB_ROOT / f"{uuid.uuid4().hex}.sqlite3"

    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-role-matrix-behavior-contract")
    monkeypatch.setenv("DEFAULT_FIRST_LOGIN_PASSWORD", "test-password")
    monkeypatch.setenv("FLASK_SKIP_SCHEMA_VALIDATION", "1")
    monkeypatch.setenv("AUTO_REPAIR_SCHEMA", "false")
    monkeypatch.setenv("STRICT_SCHEMA_CHECK", "false")
    monkeypatch.setenv("REQUIRE_DOTENV_FILE", "false")
    monkeypatch.setenv("STRICT_ENV_VALIDATION", "false")
    monkeypatch.setenv("WTF_CSRF_ENABLED", "false")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + db_path.as_posix())
    monkeypatch.setenv("MAIL_SUPPRESS_SEND", "true")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    monkeypatch.setenv("LOGIN_FORCE_CAPTCHA_FOR_UNKNOWN_USER", "false")
    for key, value in env_overrides.items():
        monkeypatch.setenv(key, value)

    from app import create_app
    from config import Config

    monkeypatch.setattr(Config, "APP_ENV", "testing")
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite:///" + db_path.as_posix())
    monkeypatch.setattr(Config, "SQLALCHEMY_ENGINE_OPTIONS", {})

    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI="sqlite:///" + db_path.as_posix(),
    )

    from app.extensions import db

    with app.app_context():
        db.create_all()

    return app


@pytest.fixture
def app(monkeypatch):
    return _make_app(monkeypatch)


def _module_setting_value(*, setting_key):
    from app.models import ModuleSetting
    row = ModuleSetting.query.filter_by(module_key="assistant", setting_key=setting_key).first()
    return None if row is None else row.value_text


def _mock_get_assistant_settings(monkeypatch, payload):
    """Both implementations do `from app.services.assistant_settings_service import
    get_assistant_settings` INSIDE their own function bodies (not at module level), so
    patching the attribute on the source module affects both call sites' next invocation --
    there is no per-module-cached binding to route around."""
    monkeypatch.setattr(
        "app.services.assistant_settings_service.get_assistant_settings",
        lambda: payload,
    )


def _raise_get_assistant_settings(monkeypatch):
    def _raise():
        raise RuntimeError("simulated get_assistant_settings failure")
    monkeypatch.setattr("app.services.assistant_settings_service.get_assistant_settings", _raise)


# ---------------------------------------------------------------------------
# A. Shared-constant sanity: both implementations must agree on the role
# universe for the rest of these tests to be comparing like-for-like.
# ---------------------------------------------------------------------------


def test_role_option_catalog_and_defaults_identical_between_implementations(app):
    with app.app_context():
        from app.main_handlers.account_communication_helpers import (
            ASSISTANT_DEFAULT_VISIBLE_ROLES as communication_defaults,
            ASSISTANT_POLICY_ROLE_OPTIONS as communication_options,
        )
        from app.main_handlers.account_settings_helpers import (
            ASSISTANT_DEFAULT_VISIBLE_ROLES as settings_defaults,
            ASSISTANT_POLICY_ROLE_OPTIONS as settings_options,
        )

        assert settings_options == communication_options
        assert settings_defaults == communication_defaults
        assert settings_defaults == {
            "admin", "baskan", "baskan_yardimcisi", "grup_baskani",
            "mali_musavir", "koordinator", "birim_sorumlusu",
        }


# ---------------------------------------------------------------------------
# B. Full-stack, real (unmocked) get_assistant_settings() against a genuinely
# empty DB -- what a never-configured install actually shows today.
# ---------------------------------------------------------------------------


def test_settings_visible_roles_on_fresh_unconfigured_db_returns_default_seven(app):
    with app.app_context():
        from app.main_handlers.account_settings_helpers import (
            ASSISTANT_DEFAULT_VISIBLE_ROLES,
            _assistant_visible_roles_from_settings,
        )
        assert _assistant_visible_roles_from_settings() == ASSISTANT_DEFAULT_VISIBLE_ROLES


def test_communication_visible_roles_on_fresh_unconfigured_db_returns_default_seven(app):
    with app.app_context():
        from app.main_handlers.account_communication_helpers import (
            ASSISTANT_DEFAULT_VISIBLE_ROLES,
            _assistant_visible_roles_from_settings,
        )
        # Currently identical to the settings side -- NOT because this
        # implementation's own fallback fired, but because
        # assistant_settings_service.get_assistant_settings() never hands back
        # an empty "visible_roles" string in the first place (it has its own
        # ASSISTANT_ALLOWED_ROLES fallback upstream). See section C below for
        # this implementation's OWN fallback behavior in isolation.
        assert _assistant_visible_roles_from_settings() == ASSISTANT_DEFAULT_VISIBLE_ROLES


# ---------------------------------------------------------------------------
# C. Isolated wrapper-logic behavior: get_assistant_settings() mocked to hand
# back exactly the payload under test, bypassing its own upstream defaulting,
# so each implementation's OWN parsing/fallback code is what's on trial.
# ---------------------------------------------------------------------------


def test_settings_role_matrix_current_null_behavior_contract(app, monkeypatch):
    """Pre-consolidation behavior lock: settings' own fallback DOES trigger on
    an empty raw visible_roles string."""
    with app.app_context():
        from app.main_handlers.account_settings_helpers import (
            ASSISTANT_DEFAULT_VISIBLE_ROLES,
            _assistant_visible_roles_from_settings,
        )
        _mock_get_assistant_settings(monkeypatch, {"visible_roles": ""})
        assert _assistant_visible_roles_from_settings() == ASSISTANT_DEFAULT_VISIBLE_ROLES


def test_communication_role_matrix_current_null_behavior_contract(app, monkeypatch):
    """Pre-consolidation behavior lock: communication's own fallback does NOT
    trigger on an empty raw visible_roles string -- this is the actual,
    currently-real divergence from the settings side (distinct from the
    dead-code null-guard line noted in the module docstring above)."""
    with app.app_context():
        from app.main_handlers.account_communication_helpers import (
            _assistant_visible_roles_from_settings,
        )
        _mock_get_assistant_settings(monkeypatch, {"visible_roles": ""})
        assert _assistant_visible_roles_from_settings() == set()


def test_settings_role_matrix_current_exception_behavior_contract(app, monkeypatch):
    with app.app_context():
        from app.main_handlers.account_settings_helpers import (
            ASSISTANT_DEFAULT_VISIBLE_ROLES,
            _assistant_visible_roles_from_settings,
        )
        _raise_get_assistant_settings(monkeypatch)
        assert _assistant_visible_roles_from_settings() == ASSISTANT_DEFAULT_VISIBLE_ROLES


def test_communication_role_matrix_current_exception_behavior_contract(app, monkeypatch):
    """Convergent with the settings side (NOT a divergence): both fall back to
    the same 7 default roles when the settings fetch itself raises."""
    with app.app_context():
        from app.main_handlers.account_communication_helpers import (
            ASSISTANT_DEFAULT_VISIBLE_ROLES,
            _assistant_visible_roles_from_settings,
        )
        _raise_get_assistant_settings(monkeypatch)
        assert _assistant_visible_roles_from_settings() == ASSISTANT_DEFAULT_VISIBLE_ROLES


@pytest.mark.parametrize("impl_module", ["account_settings_helpers", "account_communication_helpers"])
def test_visible_roles_populated_multi_role_via_mock(app, monkeypatch, impl_module):
    with app.app_context():
        module = __import__(f"app.main_handlers.{impl_module}", fromlist=["_assistant_visible_roles_from_settings"])
        _mock_get_assistant_settings(monkeypatch, {"visible_roles": "admin,personel"})
        assert module._assistant_visible_roles_from_settings() == {"admin", "personel"}


@pytest.mark.parametrize("impl_module", ["account_settings_helpers", "account_communication_helpers"])
def test_visible_roles_none_sentinel_via_mock(app, monkeypatch, impl_module):
    """Both implementations agree: an explicit "__none__" stored value (what
    save_assistant_role_matrix_from_form persists when zero roles are
    selected) resolves to an empty visible-roles set, not the default set."""
    with app.app_context():
        module = __import__(f"app.main_handlers.{impl_module}", fromlist=["_assistant_visible_roles_from_settings"])
        _mock_get_assistant_settings(monkeypatch, {"visible_roles": "__none__"})
        assert module._assistant_visible_roles_from_settings() == set()


@pytest.mark.parametrize("impl_module", ["account_settings_helpers", "account_communication_helpers"])
def test_visible_roles_normalization_via_mock(app, monkeypatch, impl_module):
    """Locks the shared (identical in both files) normalization behavior:
    whitespace-trimmed, lower-cased, dash-to-underscore."""
    with app.app_context():
        module = __import__(f"app.main_handlers.{impl_module}", fromlist=["_assistant_visible_roles_from_settings"])
        _mock_get_assistant_settings(monkeypatch, {"visible_roles": " ADMIN , Baskan-Yardimcisi ,,"})
        assert module._assistant_visible_roles_from_settings() == {"admin", "baskan_yardimcisi"}


# ---------------------------------------------------------------------------
# D. _build_assistant_role_matrix() output shape and ordering.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("impl_module", ["account_settings_helpers", "account_communication_helpers"])
def test_build_role_matrix_output_shape_and_ordering(app, monkeypatch, impl_module):
    with app.app_context():
        module = __import__(
            f"app.main_handlers.{impl_module}",
            fromlist=["_build_assistant_role_matrix", "ASSISTANT_POLICY_ROLE_OPTIONS", "ASSISTANT_DEFAULT_VISIBLE_ROLES"],
        )
        _mock_get_assistant_settings(monkeypatch, {"visible_roles": "admin,personel"})

        result = module._build_assistant_role_matrix()

        assert set(result.keys()) == {"roles", "rows", "items", "item_count", "visible_roles"}
        assert result["visible_roles"] == sorted({"admin", "personel"})
        assert result["rows"] is result["items"]
        assert result["item_count"] == len(result["items"]) == 1

        # role_rows order is deterministic: it follows ASSISTANT_POLICY_ROLE_OPTIONS'
        # fixed declaration order, not sorted() and not visible-first.
        expected_role_key_order = [role_key for role_key, _label in module.ASSISTANT_POLICY_ROLE_OPTIONS]
        assert [row["role_key"] for row in result["roles"]] == expected_role_key_order

        admin_row = next(row for row in result["roles"] if row["role_key"] == "admin")
        personel_row = next(row for row in result["roles"] if row["role_key"] == "personel")
        baskan_row = next(row for row in result["roles"] if row["role_key"] == "baskan")
        assert admin_row["visible_count"] == 1
        assert personel_row["visible_count"] == 1
        assert baskan_row["visible_count"] == 0
        assert admin_row["recommended_count"] == 1  # admin is in ASSISTANT_DEFAULT_VISIBLE_ROLES
        assert personel_row["recommended_count"] == 0  # personel is not

        item = result["items"][0]
        assert item["key"] == "assistant_module"
        assert item["visible_count"] == 2  # admin + personel
        assert [state["role_key"] for state in item["states"]] == expected_role_key_order
        assert {r for r in item["recommended_roles"]}  # non-empty: recommended labels present


# ---------------------------------------------------------------------------
# E. save_assistant_role_matrix_from_form() -- direct call, real DB, single
# commit. READ_ONLY: no. Both implementations commit once, after both the
# "enabled" and "visible_roles" module_settings rows are staged.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("impl_module", ["account_settings_helpers", "account_communication_helpers"])
def test_save_role_matrix_persists_selected_roles_and_returns_count(app, impl_module):
    with app.app_context():
        module = __import__(f"app.main_handlers.{impl_module}", fromlist=["save_assistant_role_matrix_from_form"])

        form = {
            "assistant_role_policy__admin__assistant_module": "on",
            "assistant_role_policy__personel__assistant_module": "on",
        }
        selected_count = module.save_assistant_role_matrix_from_form(form, updated_by_user_id=None)

        assert selected_count == 2
        assert _module_setting_value(setting_key="visible_roles") == "admin,personel"
        assert _module_setting_value(setting_key="enabled") == "true"


@pytest.mark.parametrize("impl_module", ["account_settings_helpers", "account_communication_helpers"])
def test_save_role_matrix_with_no_roles_selected_persists_none_sentinel(app, impl_module):
    with app.app_context():
        module = __import__(f"app.main_handlers.{impl_module}", fromlist=["save_assistant_role_matrix_from_form"])

        selected_count = module.save_assistant_role_matrix_from_form({}, updated_by_user_id=None)

        assert selected_count == 0
        assert _module_setting_value(setting_key="visible_roles") == "__none__"


# ---------------------------------------------------------------------------
# F. reset_assistant_role_matrix_defaults() -- direct call, real DB.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("impl_module", ["account_settings_helpers", "account_communication_helpers"])
def test_reset_role_matrix_persists_and_returns_default_roles(app, impl_module):
    with app.app_context():
        module = __import__(
            f"app.main_handlers.{impl_module}",
            fromlist=["reset_assistant_role_matrix_defaults", "save_assistant_role_matrix_from_form", "ASSISTANT_DEFAULT_VISIBLE_ROLES"],
        )

        # Move it away from the default first so the reset is a real assertion.
        module.save_assistant_role_matrix_from_form(
            {"assistant_role_policy__personel__assistant_module": "on"}, updated_by_user_id=None,
        )
        assert _module_setting_value(setting_key="visible_roles") == "personel"

        returned_count = module.reset_assistant_role_matrix_defaults(updated_by_user_id=None)

        assert returned_count == len(module.ASSISTANT_DEFAULT_VISIBLE_ROLES) == 7
        restored = set((_module_setting_value(setting_key="visible_roles") or "").split(","))
        assert restored == module.ASSISTANT_DEFAULT_VISIBLE_ROLES
        assert _module_setting_value(setting_key="enabled") == "true"
