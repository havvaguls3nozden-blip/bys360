"""BYS360 Daily Weather Mail -- menu visibility side-effect defect, urgent
narrow fix.

Root cause (proven mechanically, not assumed -- see this mandate's Phase A
evidence): `current_config()` unconditionally called
`ensure_daily_weather_defaults()`, which writes `RoleMenuDefault` rows for
this feature's OWN menu key (`daily_weather_mail`) only -- confirmed via a
direct before/after ORM dump: exactly 11 rows inserted, all
`menu_key='daily_weather_mail'`, nothing updated or removed, zero
`UserMenuPermission` rows touched. The write itself was already
additive/idempotent and correctly scoped.

The actual defect lives downstream, in
`app/services/settings/menu_profile_access.py`'s
`get_role_default_menu_keys_handler`: for a role with NO RoleMenuDefault
rows at all, it falls back to the static/policy default menu set; but the
moment ANY explicit RoleMenuDefault row exists for that role (regardless
of which menu_key), it stops falling back entirely and returns ONLY the
role's explicitly-`is_visible=True` rows. So the first time
`_ensure_role_menu_defaults()` ever wrote a single `daily_weather_mail`
row for `admin`, `admin` silently lost its previously-static-default-
derived visibility into every OTHER unrelated menu key
(`settings`, `settings_center_scheduled_jobs`, `settings_center_security`,
...) -- confirmed live via `can_access_menu` before/after.

This resolver is a deep, shared, foundational authorization component
used platform-wide; rewriting it is explicitly out of this mandate's
scope ("Do NOT weaken can_access_menu", "Do NOT rewrite the entire
settings initialization system"). The fix instead removes the
side-effecting call from `current_config()`'s read path: `current_config`
is a READ (this codebase's own docstring/registry conventions treat it as
such -- e.g. it is registered as `operation_type="EXPLAIN"` for the
Assistant V2 capability that reuses it), and every value it returns
already falls back gracefully via `get_setting_value()` when no DB row
exists yet, so it was never actually dependent on the write succeeding.
The two callers that legitimately need bootstrap-on-first-use already
trigger it themselves, independently: `save_config()` (still calls
`ensure_daily_weather_defaults()`) and the management UI route
`daily_weather_mail_settings()` in
app/communication/daily_weather_mail_routes.py (already called
`ensure_daily_weather_defaults()` explicitly, immediately before calling
`current_config()`, even before this fix) -- so this is a pure
side-effect removal with zero behavior change for either.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.ci_safe

_PASSWORD = "Assist_v2_Test_Pw_1!"

_WATCHED_KEYS = ("settings", "settings_center_scheduled_jobs", "settings_center_security")


def _mk_user(db, User, *, sicil_no, role):
    existing = User.query.filter_by(sicil_no=sicil_no).first()
    if existing is not None:
        return existing
    user = User(
        sicil_no=sicil_no, email=f"{sicil_no}@ktb.gov.tr", ad="Weather", soyad="Test",
        role=role, is_active=True, must_change_password=False, must_set_security_question=False,
    )
    user.set_password(_PASSWORD)
    db.session.add(user)
    db.session.commit()
    return user


def _snapshot(RoleMenuDefault, UserMenuPermission):
    role_rows = {
        (r.role_name, r.menu_key): (r.is_visible, r.source_type)
        for r in RoleMenuDefault.query.all()
    }
    user_rows = {
        (r.user_id, r.menu_key): (r.is_visible, r.source_type)
        for r in UserMenuPermission.query.all()
    }
    return role_rows, user_rows


@pytest.fixture
def admin(app):
    from app.extensions import db
    from app.models import User

    with app.app_context():
        yield _mk_user(db, User, sicil_no="weather_side_effect_admin", role="admin")


# ---------------------------------------------------------------------------
# Items 1-4: current_config does not revoke unrelated menu access
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("menu_key", _WATCHED_KEYS)
def test_current_config_does_not_revoke_unrelated_menu_access(app, admin, menu_key):
    """Mandate items 1-4."""
    from app.route_support import can_access_menu
    from app.services.daily_weather_mail import current_config

    with app.app_context():
        before = can_access_menu(admin, menu_key)
        current_config()
        after = can_access_menu(admin, menu_key)
    assert before == after, f"{menu_key}: access changed from {before} to {after} merely by reading weather-mail config"


# ---------------------------------------------------------------------------
# Items 5-7: explicit rows preserved, unrelated rows untouched
# ---------------------------------------------------------------------------


def test_explicit_role_menu_default_rows_preserved(app, admin):
    """Mandate item 5."""
    from app.extensions import db
    from app.models.settings_models import RoleMenuDefault
    from app.services.daily_weather_mail import current_config

    with app.app_context():
        existing = RoleMenuDefault.query.filter_by(role_name="admin", menu_key="settings").first()
        if existing is None:
            db.session.add(RoleMenuDefault(role_name="admin", menu_key="settings", is_visible=True, source_type="seed"))
            db.session.commit()

        before_row = RoleMenuDefault.query.filter_by(role_name="admin", menu_key="settings").first()
        before = (before_row.is_visible, before_row.source_type)

        current_config()

        after_row = RoleMenuDefault.query.filter_by(role_name="admin", menu_key="settings").first()
        assert after_row is not None
        assert (after_row.is_visible, after_row.source_type) == before


def test_explicit_user_menu_permission_rows_preserved(app, admin):
    """Mandate item 6."""
    from app.extensions import db
    from app.models import UserMenuPermission
    from app.services.daily_weather_mail import current_config

    with app.app_context():
        existing = UserMenuPermission.query.filter_by(user_id=admin.id, menu_key="settings").first()
        if existing is None:
            db.session.add(UserMenuPermission(user_id=admin.id, menu_key="settings", is_visible=True, source_type="user_override"))
            db.session.commit()

        before_row = UserMenuPermission.query.filter_by(user_id=admin.id, menu_key="settings").first()
        before = (before_row.is_visible, before_row.source_type)

        current_config()

        after_row = UserMenuPermission.query.filter_by(user_id=admin.id, menu_key="settings").first()
        assert after_row is not None
        assert (after_row.is_visible, after_row.source_type) == before


def test_unrelated_menu_rows_untouched(app, admin):
    """Mandate item 7 -- full-table before/after diff, not spot checks."""
    from app.models import UserMenuPermission
    from app.models.settings_models import RoleMenuDefault
    from app.services.daily_weather_mail import current_config

    with app.app_context():
        before_role, before_user = _snapshot(RoleMenuDefault, UserMenuPermission)
        current_config()
        after_role, after_user = _snapshot(RoleMenuDefault, UserMenuPermission)

    non_weather_before = {k: v for k, v in before_role.items() if k[1] != "daily_weather_mail"}
    non_weather_after = {k: v for k, v in after_role.items() if k[1] != "daily_weather_mail"}
    assert non_weather_before == non_weather_after
    assert before_user == after_user


# ---------------------------------------------------------------------------
# Item 8: weather-mail-specific defaults can still be added when actually needed
# ---------------------------------------------------------------------------


def test_weather_mail_specific_defaults_still_creatable_via_existing_bootstrap_path(app, admin):
    """Mandate item 8 -- ensure_daily_weather_defaults() itself is
    untouched and still works when a caller that legitimately needs
    bootstrapping (e.g. save_config()) invokes it."""
    from app.models.settings_models import RoleMenuDefault
    from app.services.daily_weather_mail import ensure_daily_weather_defaults

    with app.app_context():
        before = RoleMenuDefault.query.filter_by(role_name="admin", menu_key="daily_weather_mail").first()
        assert before is None

        ensure_daily_weather_defaults()

        after = RoleMenuDefault.query.filter_by(role_name="admin", menu_key="daily_weather_mail").first()
        assert after is not None
        assert after.is_visible is True


# ---------------------------------------------------------------------------
# Items 9-10: idempotency
# ---------------------------------------------------------------------------


def test_repeated_current_config_calls_are_idempotent(app, admin):
    """Mandate item 9."""
    from app.services.daily_weather_mail import current_config

    with app.app_context():
        first = current_config()
        second = current_config()
        third = current_config()
    assert first == second == third


def test_repeated_ensure_daily_weather_defaults_calls_are_idempotent(app, admin):
    """Mandate item 10."""
    from app.models.settings_models import RoleMenuDefault
    from app.services.daily_weather_mail import ensure_daily_weather_defaults

    with app.app_context():
        ensure_daily_weather_defaults()
        first_count = RoleMenuDefault.query.filter_by(menu_key="daily_weather_mail").count()
        ensure_daily_weather_defaults()
        ensure_daily_weather_defaults()
        second_count = RoleMenuDefault.query.filter_by(menu_key="daily_weather_mail").count()
    assert first_count == second_count


# ---------------------------------------------------------------------------
# Item 15: session remains clean after the call
#
# Items 11-14 (Assistant V2 dispatch proof: authorized DATA_FOUND,
# authorization state stable across dispatch, unauthorized ACCESS_DENIED,
# no mutation on denial) intentionally live in
# tests/quality/test_assistant_v2_zero_arg_handler_dispatch_v1.py instead
# (mandate: test-scope split for two independent green commits). This file
# must pass with ONLY app/services/daily_weather_mail.py changed --
# `email_automation_explain_daily_weather_mail_settings` is not reachable
# via invoke_capability without the separate zero-arg dispatch fix
# (capability_registry.py + read_adapters.py), so no test here may depend
# on that capability being dispatchable.
# ---------------------------------------------------------------------------


def test_session_remains_clean_after_current_config_call(app, admin):
    """Mandate item 15."""
    from app.extensions import db
    from app.services.daily_weather_mail import current_config

    with app.app_context():
        current_config()
        # A dirty/broken session raises on the next real query; this must
        # not raise.
        from app.models import User

        User.query.filter_by(sicil_no="weather_side_effect_admin").first()
        assert db.session.is_active
