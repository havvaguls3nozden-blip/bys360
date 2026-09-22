"""BYS360 Assistant V2 -- zero-arg capability invocation defect, narrow
follow-up (layered on top of the technical-field-humanization commit,
c2443c80).

Root cause (proven live, not assumed): `capability_dispatcher.invoke_capability`
always calls a registered handler as `handler(user, **kwargs)` -- the
uniform calling contract `read_adapters.py`'s own module docstring already
documents ("Takes the current authenticated `user` object as its first
argument ... This keeps every adapter's call signature uniform for a
future router/dispatcher layer"). Three capabilities' `service_handler`
pointed directly at a REUSED, already-shipped service function that takes
NO parameters at all (confirmed via `inspect.signature`):

  - ai_decision_support_explain_governance_settings -> get_ai_governance_settings()
  - virtual_assistant_explain_role_matrix -> build_assistant_role_matrix()
  - email_automation_explain_daily_weather_mail_settings -> current_config()

Calling `handler(user)` against any of these raised a real `TypeError`,
caught by `invoke_capability`'s existing fail-closed exception handling
and turned into `SYSTEM_ERROR` -- reproduced live before this fix via
direct `handler(admin)` calls (see the mandate's Phase A evidence).

Fix (Option A, adapter wrappers -- the architecture this project's own
read_adapters.py docstring already establishes as the intended pattern):
three new, thin `(user, **kwargs)`-shaped wrapper functions added to
`read_adapters.py`, each forwarding to the exact same, unmodified reused
function. `capability_registry.py`'s three `service_handler` entries now
point at these wrappers instead of the raw reused functions.
`capability_dispatcher.py` itself is completely untouched -- its
`handler(user, **kwargs)` calling contract, its authorization gate
(`_is_authorized`, checked strictly BEFORE any handler call), and its
existing fail-closed exception handling (any handler exception, including
a genuine internal TypeError, becomes SYSTEM_ERROR -- never retried,
never silently reinterpreted) are all unchanged and reproven below.
"""
from __future__ import annotations

import inspect

import pytest

pytestmark = pytest.mark.ci_safe

_PASSWORD = "Assist_v2_Test_Pw_1!"

_TOUCHED_CAPABILITIES = (
    "ai_decision_support_explain_governance_settings",
    "virtual_assistant_explain_role_matrix",
    "email_automation_explain_daily_weather_mail_settings",
)


def _mk_user(db, User, *, sicil_no, role):
    existing = User.query.filter_by(sicil_no=sicil_no).first()
    if existing is not None:
        return existing
    user = User(
        sicil_no=sicil_no, email=f"{sicil_no}@ktb.gov.tr", ad="ZeroArg", soyad="Hotfix",
        role=role, is_active=True, must_change_password=False, must_set_security_question=False,
    )
    user.set_password(_PASSWORD)
    db.session.add(user)
    db.session.commit()
    return user


def _grant_menu(db, RoleMenuDefault, *, role_name, menu_key):
    """Deterministic test-only authorization seed -- mirrors exactly what
    a real admin configures through Settings > Role Matrix. Needed because
    ai_center/ai_agent_panel visibility is resolved live from
    RoleMenuDefault rows with no code-level admin bypass (confirmed:
    app/route_support.py's own comment -- "Admin/üst rol bypassı
    kaldırıldı")."""
    existing = RoleMenuDefault.query.filter_by(role_name=role_name, menu_key=menu_key).first()
    if existing is None:
        db.session.add(RoleMenuDefault(role_name=role_name, menu_key=menu_key, is_visible=True, source_type="seed"))
    else:
        existing.is_visible = True
    db.session.commit()


@pytest.fixture
def authorized_admin(app):
    from app.extensions import db
    from app.models import User
    from app.models.settings_models import RoleMenuDefault

    with app.app_context():
        admin = _mk_user(db, User, sicil_no="zero_arg_authorized_admin", role="admin")
        _grant_menu(db, RoleMenuDefault, role_name="admin", menu_key="ai_center")
        _grant_menu(db, RoleMenuDefault, role_name="admin", menu_key="ai_agent_panel")
        yield admin


@pytest.fixture
def unauthorized_personel(app):
    from app.extensions import db
    from app.models import User

    with app.app_context():
        yield _mk_user(db, User, sicil_no="zero_arg_unauthorized_personel", role="personel")


# ---------------------------------------------------------------------------
# Items 1-4: no more TypeError, all 3 dispatch through invoke_capability
# ---------------------------------------------------------------------------


def test_governance_settings_dispatch_no_longer_typeerrors(app, authorized_admin):
    """Mandate item 1."""
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    with app.app_context():
        result = invoke_capability(authorized_admin, "ai_decision_support_explain_governance_settings")
    assert result.status is AssistantResultStatus.DATA_FOUND
    assert isinstance(result.data, dict)
    assert "module_quality_floor" in result.data


def test_role_matrix_dispatch_no_longer_typeerrors(app, authorized_admin):
    """Mandate item 2."""
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    with app.app_context():
        result = invoke_capability(authorized_admin, "virtual_assistant_explain_role_matrix")
    assert result.status is AssistantResultStatus.DATA_FOUND
    assert isinstance(result.data, dict)
    assert "visible_roles" in result.data


def test_weather_mail_settings_dispatch_no_longer_typeerrors(app, authorized_admin):
    """Mandate item 3."""
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    with app.app_context():
        result = invoke_capability(authorized_admin, "email_automation_explain_daily_weather_mail_settings")
    assert result.status is AssistantResultStatus.DATA_FOUND
    assert isinstance(result.data, dict)
    assert "enabled" in result.data


def test_all_three_work_through_invoke_capability_not_only_direct_call(app, authorized_admin):
    """Mandate item 4 -- explicit proof this goes through the real
    dispatcher (authorization + handler resolution + call), not a
    hand-picked direct function call."""
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    with app.app_context():
        for cap_key in _TOUCHED_CAPABILITIES:
            result = invoke_capability(authorized_admin, cap_key)
            assert result.status is AssistantResultStatus.DATA_FOUND, cap_key
            assert result.capability_key == cap_key


# ---------------------------------------------------------------------------
# Items 5-9: authorization gate unchanged, fail-closed, underlying service
# never reached when denied
# ---------------------------------------------------------------------------


def test_unauthorized_governance_request_remains_access_denied(app, unauthorized_personel):
    """Mandate item 6."""
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    with app.app_context():
        result = invoke_capability(unauthorized_personel, "ai_decision_support_explain_governance_settings")
    assert result.status is AssistantResultStatus.ACCESS_DENIED


def test_unauthorized_role_matrix_request_remains_access_denied(app, unauthorized_personel, monkeypatch):
    """Mandate item 7. `ai_agent_panel` (this capability's permission_key)
    is, by real, intentional product policy, broadly granted to every
    authenticated role by default (the AI assistant panel itself is not
    admin-only) -- confirmed live: `personel` alone does not reproduce a
    denial. The authorization MECHANISM is proven deterministically
    instead, by forcing `can_access_menu` to deny for this one call, the
    same function `_is_authorized` always calls for a permission_key
    capability -- not a new check invented for this test."""
    import app.services.assistant_v2.capability_dispatcher as dispatcher_module
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    monkeypatch.setattr(dispatcher_module, "can_access_menu", lambda user, menu_key: False)
    with app.app_context():
        result = dispatcher_module.invoke_capability(unauthorized_personel, "virtual_assistant_explain_role_matrix")
    assert result.status is AssistantResultStatus.ACCESS_DENIED


def test_unauthorized_weather_settings_request_remains_access_denied(app, unauthorized_personel):
    """Mandate item 8."""
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    with app.app_context():
        result = invoke_capability(unauthorized_personel, "email_automation_explain_daily_weather_mail_settings")
    assert result.status is AssistantResultStatus.ACCESS_DENIED


@pytest.mark.parametrize(
    "cap_key,patch_target",
    [
        ("ai_decision_support_explain_governance_settings", "app.services.ai.governance_settings.get_ai_governance_settings"),
        ("virtual_assistant_explain_role_matrix", "app.services.assistant_role_matrix_service.build_assistant_role_matrix"),
        ("email_automation_explain_daily_weather_mail_settings", "app.services.daily_weather_mail.current_config"),
    ],
)
def test_underlying_service_not_called_when_access_denied(app, unauthorized_personel, monkeypatch, cap_key, patch_target):
    """Mandate items 5 and 9 -- authorization is checked strictly BEFORE
    any handler call: a spy replacing the real underlying function must
    never be invoked for a denied caller."""
    import app.services.assistant_v2.capability_dispatcher as dispatcher_module
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    calls: list[int] = []
    module_path, _, attr = patch_target.rpartition(".")
    module = __import__(module_path, fromlist=[attr])

    def _spy(*args, **kwargs):
        calls.append(1)
        return {}

    with app.app_context():
        monkeypatch.setattr(module, attr, _spy)
        if cap_key == "virtual_assistant_explain_role_matrix":
            # ai_agent_panel is broadly granted by real policy -- force the
            # denial deterministically (see
            # test_unauthorized_role_matrix_request_remains_access_denied
            # for why), rather than depending on live menu-seed state.
            monkeypatch.setattr(dispatcher_module, "can_access_menu", lambda user, menu_key: False)
        result = dispatcher_module.invoke_capability(unauthorized_personel, cap_key)
        assert result.status is AssistantResultStatus.ACCESS_DENIED
        assert calls == [], f"{cap_key}: underlying service was called despite ACCESS_DENIED"


# ---------------------------------------------------------------------------
# Items 10-11: no TypeError-retry fallback exists; a genuine internal
# TypeError still surfaces as a real failure
# ---------------------------------------------------------------------------


def test_no_typeerror_retry_fallback_exists_in_dispatcher_source():
    """Mandate item 10 -- static proof: capability_dispatcher.py contains
    no `except TypeError` swallow-and-retry pattern anywhere (the
    prohibited solution this mandate explicitly forbids)."""
    import app.services.assistant_v2.capability_dispatcher as dispatcher_module

    source = inspect.getsource(dispatcher_module)
    assert "except TypeError" not in source
    assert "handler()" not in source  # no bare zero-arg retry call anywhere


@pytest.mark.parametrize(
    "cap_key,patch_target",
    [
        ("ai_decision_support_explain_governance_settings", "app.services.ai.governance_settings.get_ai_governance_settings"),
        ("virtual_assistant_explain_role_matrix", "app.services.assistant_role_matrix_service.build_assistant_role_matrix"),
        ("email_automation_explain_daily_weather_mail_settings", "app.services.daily_weather_mail.current_config"),
    ],
)
def test_genuine_internal_typeerror_still_surfaces_as_system_error(app, authorized_admin, monkeypatch, cap_key, patch_target):
    """Mandate item 11 -- a REAL bug inside the underlying, already-
    authorized handler call (simulated here as a TypeError raised from
    within the reused function itself, e.g. a future regression) must
    still be treated as a genuine failure (SYSTEM_ERROR, fail-closed),
    never silently reinterpreted as an invocation-signature mismatch or
    retried with a different call shape."""
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    module_path, _, attr = patch_target.rpartition(".")
    module = __import__(module_path, fromlist=[attr])

    def _boom(*args, **kwargs):
        raise TypeError("simulated genuine internal defect, not a signature mismatch")

    with app.app_context():
        monkeypatch.setattr(module, attr, _boom)
        result = invoke_capability(authorized_admin, cap_key)
        assert result.status is AssistantResultStatus.SYSTEM_ERROR


# ---------------------------------------------------------------------------
# Items 12-15: contracts preserved
# ---------------------------------------------------------------------------


def test_structured_result_contract_preserved(app, authorized_admin):
    """Mandate item 12 -- the wrapper forwards to the unmodified reused
    function; its returned dict shape must be untouched."""
    from app.services.ai.governance_settings import get_ai_governance_settings
    from app.services.assistant_v2.capability_dispatcher import invoke_capability

    with app.app_context():
        direct = get_ai_governance_settings()
        result = invoke_capability(authorized_admin, "ai_decision_support_explain_governance_settings")
    assert result.data == direct


def test_response_humanization_from_c2443c80_remains_intact(app, authorized_admin):
    """Mandate item 13 -- the role-matrix formatter added in c2443c80
    must still produce a natural, non-raw-key answer once the dispatcher
    can actually reach real data (it could not before this follow-up)."""
    from app.services.assistant_v2 import response_composer
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantCapabilityResult

    with app.app_context():
        dispatch_result = invoke_capability(authorized_admin, "virtual_assistant_explain_role_matrix")
        result = AssistantCapabilityResult(
            status=dispatch_result.status, message=dispatch_result.message,
            capability_key="virtual_assistant_explain_role_matrix", module_key="virtual_assistant",
            data=dispatch_result.data, source_label="Asistan Rol Matrisi",
        )
        composed = response_composer.compose_response(result)
    assert "visible_roles" not in composed.answer_text
    assert "role_key" not in composed.answer_text
    assert "görünür" in composed.answer_text


def test_web_presentation_compatible(app, authorized_admin):
    """Mandate item 14."""
    from app.services.assistant_v2 import response_composer
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantCapabilityResult
    from app.services.assistant_v2.web_presentation_adapter import adapt_for_legacy_web

    with app.app_context(), app.test_request_context():
        dispatch_result = invoke_capability(authorized_admin, "email_automation_explain_daily_weather_mail_settings")
        result = AssistantCapabilityResult(
            status=dispatch_result.status, message=dispatch_result.message,
            capability_key="email_automation_explain_daily_weather_mail_settings", module_key="email_automation",
            data=dispatch_result.data, source_label="Günlük Bilgilendirme E-postası Ayarı",
        )
        composed = response_composer.compose_response(result)

        class _FakeAnswer:
            status = "DATA_FOUND"
            answer = composed.answer_text
            module_keys = ("email_automation",)
            capability_key = "email_automation_explain_daily_weather_mail_settings"
            sources = ()
            conversation_id = None
            clarification = None
            related_links = ()

        web = adapt_for_legacy_web(_FakeAnswer())
    assert "recipient_user_ids" not in web["answer"]
    assert web["answer"]


def test_mobile_presentation_compatible(app, authorized_admin):
    """Mandate item 15."""
    from app.services.assistant_v2 import response_composer
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.mobile_presentation_adapter import adapt_for_mobile
    from app.services.assistant_v2.result_contract import AssistantCapabilityResult

    with app.app_context(), app.test_request_context():
        dispatch_result = invoke_capability(authorized_admin, "ai_decision_support_explain_governance_settings")
        result = AssistantCapabilityResult(
            status=dispatch_result.status, message=dispatch_result.message,
            capability_key="ai_decision_support_explain_governance_settings", module_key="ai_decision_support",
            data=dispatch_result.data, source_label="AI Governance Ayarı",
        )
        composed = response_composer.compose_response(result)

        class _FakeAnswer:
            status = "DATA_FOUND"
            answer = composed.answer_text
            module_keys = ("ai_decision_support",)
            capability_key = "ai_decision_support_explain_governance_settings"
            related_links = ()
            clarification = None

        mobile = adapt_for_mobile(_FakeAnswer())
    assert mobile["answer"]
    assert mobile["intent"]


# ---------------------------------------------------------------------------
# Daily-weather-mail dispatch integration (mandate: test-scope split for
# two independent green commits). These 4 tests moved here from
# tests/quality/test_daily_weather_menu_visibility_side_effect_v1.py: they
# exercise `email_automation_explain_daily_weather_mail_settings` through
# the real Assistant V2 dispatcher, which is only reachable because of
# THIS file's own zero-arg fix (capability_registry.py + read_adapters.py)
# -- so they belong to this commit's scope, not the separate
# daily_weather_mail.py side-effect fix's scope. They also incidentally
# prove the side-effect fix holds up through the dispatcher: dispatching
# this capability must not change the caller's own authorization state
# for unrelated menu keys.
# ---------------------------------------------------------------------------


def test_daily_weather_dispatch_authorized_returns_data_found(app, authorized_admin):
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    with app.app_context():
        result = invoke_capability(authorized_admin, "email_automation_explain_daily_weather_mail_settings")
    assert result.status is AssistantResultStatus.DATA_FOUND


def test_daily_weather_dispatch_authorization_state_before_after_identical(app, authorized_admin):
    from app.route_support import can_access_menu
    from app.services.assistant_v2.capability_dispatcher import invoke_capability

    watched_keys = ("settings", "settings_center_scheduled_jobs", "settings_center_security")
    with app.app_context():
        before = {key: can_access_menu(authorized_admin, key) for key in watched_keys}
        invoke_capability(authorized_admin, "email_automation_explain_daily_weather_mail_settings")
        after = {key: can_access_menu(authorized_admin, key) for key in watched_keys}
    assert before == after


def test_daily_weather_dispatch_unauthorized_remains_access_denied(app, unauthorized_personel):
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    with app.app_context():
        result = invoke_capability(unauthorized_personel, "email_automation_explain_daily_weather_mail_settings")
    assert result.status is AssistantResultStatus.ACCESS_DENIED


def test_daily_weather_dispatch_unauthorized_performs_no_configuration_mutation(app, unauthorized_personel, monkeypatch):
    import app.services.daily_weather_mail as daily_weather_mail_module
    from app.models.settings_models import RoleMenuDefault
    from app.services.assistant_v2.capability_dispatcher import invoke_capability

    calls: list[int] = []
    real_ensure = daily_weather_mail_module.ensure_daily_weather_defaults

    def _spy(*args, **kwargs):
        calls.append(1)
        return real_ensure(*args, **kwargs)

    with app.app_context():
        monkeypatch.setattr(daily_weather_mail_module, "ensure_daily_weather_defaults", _spy)
        before_count = RoleMenuDefault.query.count()
        result = invoke_capability(unauthorized_personel, "email_automation_explain_daily_weather_mail_settings")
        after_count = RoleMenuDefault.query.count()

    assert result.status.value == "ACCESS_DENIED"
    assert calls == []
    assert before_count == after_count
