"""BYS360 Assistant V2 -- intent routing + capability dispatch behavior contract.

Proves the real, enforced behavior of `app.services.assistant_v2.intent_router`
and `app.services.assistant_v2.capability_dispatcher` against the real Flask
app and a real (test) database -- not just the static registry-shape checks
in `test_assistant_v2_capability_registry_contract_v1.py`. In particular this
is where mandate Phase 6 ("permission enforcement must happen in
Python/application code BEFORE sensitive data is supplied to the model") and
Phase 9 (anti-hallucination status contract) get an actual behavioral proof:
an authorized admin gets real data, an unauthorized user is denied, an
unknown/disabled capability never silently succeeds, and a handler failure
never raises out of the dispatcher or fabricates a result.

Uses the same `app` fixture and `_create_user`-style pattern already
established by `tests/quality/test_settings_center_v2_completeness_contract_v1.py`.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.ci_safe

_PASSWORD = "Assist_v2_Test_Pw_1!"


def _create_user(app, *, sicil_no, role, password=_PASSWORD):
    from app.extensions import db
    from app.models import User

    with app.app_context():
        existing = User.query.filter_by(sicil_no=sicil_no).first()
        if existing is not None:
            return existing.id
        user = User(
            sicil_no=sicil_no,
            email=f"{sicil_no}@ktb.gov.tr",
            ad="AssistantV2",
            soyad="Contract",
            role=role,
            is_active=True,
            must_change_password=False,
            must_set_security_question=False,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


def _get_user(app, user_id):
    from app.models import User

    return User.query.get(user_id)


# ---------------------------------------------------------------------------
# A: intent_router -- routing only, no authorization, no DB
# ---------------------------------------------------------------------------


def test_resolve_intent_candidates_matches_known_personnel_query():
    from app.services.assistant_v2.intent_router import resolve_intent_candidates

    candidates = resolve_intent_candidates("personel sicil kaydını göster")
    assert "personnel_hr_read_personnel_record" in candidates


def test_resolve_intent_candidates_empty_text_returns_empty_list():
    from app.services.assistant_v2.intent_router import resolve_intent_candidates

    assert resolve_intent_candidates("") == []
    assert resolve_intent_candidates("   ") == []


def test_resolve_intent_candidates_gibberish_returns_empty_list():
    """A query that overlaps with no registered intent_tags at all must come
    back empty -- this is what lets a caller correctly report
    AMBIGUOUS_REQUEST instead of guessing a capability."""
    from app.services.assistant_v2.intent_router import resolve_intent_candidates

    assert resolve_intent_candidates("qwertyzxcvbnmasdfgh") == []


def test_resolve_intent_candidates_respects_max_candidates():
    from app.services.assistant_v2.intent_router import resolve_intent_candidates

    candidates = resolve_intent_candidates("liste kayıt özet", max_candidates=2)
    assert len(candidates) <= 2


def test_resolve_intent_candidates_module_scoped():
    from app.services.assistant_v2.capability_registry import get_capability
    from app.services.assistant_v2.intent_router import resolve_intent_candidates

    candidates = resolve_intent_candidates("liste kayıt", module_key="performance_mgmt")
    for key in candidates:
        entry = get_capability(key)
        assert entry is not None
        assert entry.module_key == "performance_mgmt"


def test_resolve_module_candidates_matches_known_query():
    from app.services.assistant_v2.intent_router import resolve_module_candidates

    candidates = resolve_module_candidates("bekleyen izin taleplerini göster")
    assert "personnel_hr" in candidates


def test_intent_router_does_not_import_database_layer():
    """Architectural guard: intent_router must stay a pure text-scoring
    module with no DB/Flask-request access -- routing must not grant access
    or touch data, per the mandate's own Phase 5 text."""
    import ast
    from pathlib import Path

    source = Path("app/services/assistant_v2/intent_router.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
    forbidden = {"app.extensions", "flask_sqlalchemy", "sqlalchemy"}
    assert not (imported_modules & forbidden), (
        f"intent_router.py imported a DB-layer module: {imported_modules & forbidden}"
    )


# ---------------------------------------------------------------------------
# B: capability_dispatcher -- the real authorization gate
# ---------------------------------------------------------------------------


def test_invoke_capability_unknown_key_is_capability_unavailable(app):
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    admin_id = _create_user(app, sicil_no="av2_disp_admin", role="admin")
    with app.app_context():
        user = _get_user(app, admin_id)
        result = invoke_capability(user, "this_capability_key_does_not_exist_anywhere")
    assert result.status is AssistantResultStatus.CAPABILITY_UNAVAILABLE


def test_invoke_capability_self_describing_available_to_any_authenticated_user(app):
    """virtual_assistant_discover_available_modules is is_self_describing --
    it must be reachable by ANY authenticated user regardless of role, since
    it only enumerates access, it never grants it."""
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    personel_id = _create_user(app, sicil_no="av2_disp_personel_self", role="personel")
    with app.app_context():
        user = _get_user(app, personel_id)
        result = invoke_capability(user, "virtual_assistant_discover_available_modules")
    assert result.status in (AssistantResultStatus.DATA_FOUND, AssistantResultStatus.NO_DATA)
    assert result.status is not AssistantResultStatus.ACCESS_DENIED


def test_invoke_capability_admin_gated_capability_denies_personel_role(app):
    """personnel_hr_read_personnel_record requires the real 'admin_users'
    menu key -- a plain 'personel' role must be denied, not silently served
    with restricted data (Phase 6: deny, don't filter after the fact)."""
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    personel_id = _create_user(app, sicil_no="av2_disp_personel_denied", role="personel")
    with app.app_context():
        user = _get_user(app, personel_id)
        result = invoke_capability(user, "personnel_hr_read_personnel_record", sicil_no="does_not_matter")
    assert result.status is AssistantResultStatus.ACCESS_DENIED
    assert result.data is None


def test_invoke_capability_admin_gated_capability_allows_admin_role(app):
    """The same capability must NOT deny an admin -- proves the gate is a
    real, working permission check, not an unconditional deny."""
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    admin_id = _create_user(app, sicil_no="av2_disp_admin_allowed", role="admin")
    with app.app_context():
        user = _get_user(app, admin_id)
        result = invoke_capability(user, "personnel_hr_read_personnel_record", sicil_no="__nonexistent_sicil__")
    assert result.status is not AssistantResultStatus.ACCESS_DENIED
    assert result.status is AssistantResultStatus.NO_DATA


def test_invoke_capability_file_center_auth_override_denies_non_admin(app):
    """file_center_read_quota_status uses the documented auth_override
    (can_manage_file_center_settings), not a menu_key -- confirm the
    override path itself actually denies a low-privilege role."""
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    personel_id = _create_user(app, sicil_no="av2_disp_fc_personel", role="personel")
    with app.app_context():
        user = _get_user(app, personel_id)
        result = invoke_capability(user, "file_center_read_quota_status")
    assert result.status is AssistantResultStatus.ACCESS_DENIED


def test_invoke_capability_admin_role_family_override_denies_non_admin(app):
    """email_automation_summarize_performance_reminder_health uses the
    admin_required_role_family override -- confirm it denies a role outside
    ADMIN_FAMILY_ROLES."""
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    personel_id = _create_user(app, sicil_no="av2_disp_email_personel", role="personel")
    with app.app_context():
        user = _get_user(app, personel_id)
        result = invoke_capability(user, "email_automation_summarize_performance_reminder_health")
    assert result.status is AssistantResultStatus.ACCESS_DENIED


def test_invoke_capability_disabled_module_is_capability_unavailable(app, monkeypatch):
    """Even a capability with valid permission_key must be refused if its
    OWN module is inactive in MODULE_REGISTRY -- proves module-level
    disablement is checked, not only capability-level."""
    from app.services.assistant_v2 import capability_dispatcher
    from app.services.assistant_v2.result_contract import AssistantResultStatus
    from app.services.settings import module_registry

    real_entry = module_registry.get_module("personnel_hr")
    disabled_entry = module_registry.ModuleRegistryEntry(**{**real_entry.__dict__, "active": False})
    monkeypatch.setattr(
        capability_dispatcher,
        "get_module",
        lambda module_key: disabled_entry if module_key == "personnel_hr" else module_registry.get_module(module_key),
    )

    admin_id = _create_user(app, sicil_no="av2_disp_disabled_module", role="admin")
    with app.app_context():
        user = _get_user(app, admin_id)
        result = capability_dispatcher.invoke_capability(user, "personnel_hr_read_personnel_record", sicil_no="x")
    assert result.status is AssistantResultStatus.CAPABILITY_UNAVAILABLE


def test_invoke_capability_handler_exception_is_system_error_not_a_crash(app, monkeypatch):
    """If the underlying service_handler raises, the dispatcher must return
    SYSTEM_ERROR -- never let the exception propagate, and never fabricate a
    DATA_FOUND result to paper over the failure (Phase 19)."""
    from app.services.assistant_v2 import capability_dispatcher
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    def _boom(user, **kwargs):
        raise RuntimeError("simulated handler failure for test coverage")

    monkeypatch.setattr(capability_dispatcher, "_resolve_handler", lambda service_handler: _boom)

    admin_id = _create_user(app, sicil_no="av2_disp_handler_boom", role="admin")
    with app.app_context():
        user = _get_user(app, admin_id)
        result = capability_dispatcher.invoke_capability(user, "personnel_hr_read_personnel_record", sicil_no="x")
    assert result.status is AssistantResultStatus.SYSTEM_ERROR
    assert result.data is None
    assert "RuntimeError" not in result.message
    assert "simulated handler failure" not in result.message


def test_invoke_capability_never_raises_for_anonymous_user(app):
    """An unauthenticated/None-like user must be denied, not crash the
    dispatcher with an AttributeError."""
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    with app.app_context():
        result = invoke_capability(None, "personnel_hr_read_personnel_record", sicil_no="x")
    assert result.status is AssistantResultStatus.ACCESS_DENIED


def test_invoke_capability_message_never_leaks_permission_key_or_service_handler(app):
    """The denial message shown to the user must stay generic -- it must
    never echo the internal permission_key or service_handler dotted path
    (Phase 11: explain access denial safely, without exposing policy
    internals)."""
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.capability_registry import get_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    personel_id = _create_user(app, sicil_no="av2_disp_msg_leak", role="personel")
    with app.app_context():
        user = _get_user(app, personel_id)
        result = invoke_capability(user, "personnel_hr_read_personnel_record", sicil_no="x")
        entry = get_capability("personnel_hr_read_personnel_record")
    assert entry is not None
    assert result.status is AssistantResultStatus.ACCESS_DENIED
    assert entry.permission_key and entry.permission_key not in result.message
    assert entry.service_handler not in result.message
