"""BYS360 Assistant V2 -- procedural guide contract (mandate Phase B/C/D:
legacy procedural-help migration + trusted related-link resolution).
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
            sicil_no=sicil_no, email=f"{sicil_no}@ktb.gov.tr", ad="Guide", soyad="Test",
            role=role, is_active=True, must_change_password=False, must_set_security_question=False,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


def _get_user(app, user_id):
    from app.models import User

    return User.query.get(user_id)


def _login(client, sicil_no, password=_PASSWORD):
    client.get("/logout", follow_redirects=False)
    response = client.post("/login", data={"sicil_or_email": sicil_no, "password": password}, follow_redirects=False)
    assert response.status_code == 302
    return response


def _ask(client, question, **extra):
    response = client.post("/ai-agent/api/v2/ask", json={"question": question, **extra})
    assert response.status_code == 200
    return response.get_json()


# ---------------------------------------------------------------------------
# Registry completeness
# ---------------------------------------------------------------------------


def test_procedural_guide_registry_has_no_duplicate_keys():
    from app.services.assistant_v2.procedural_guides import find_duplicate_guide_keys

    assert find_duplicate_guide_keys() == []


def test_procedural_guide_registry_has_no_orphan_module_keys():
    from app.services.assistant_v2.procedural_guides import find_guides_with_orphan_module_key

    assert find_guides_with_orphan_module_key() == []


def test_procedural_guide_registry_every_active_entry_has_steps():
    from app.services.assistant_v2.procedural_guides import list_active_guides

    for entry in list_active_guides():
        assert len(entry.steps) > 0, f"{entry.guide_key} has no steps"


# ---------------------------------------------------------------------------
# Routing: guides never steal a genuine data-capability query
# ---------------------------------------------------------------------------


def test_procedural_question_routes_to_guide_at_high_confidence():
    from app.services.assistant_v2.guide_intent_router import resolve_guide_intent
    from app.services.assistant_v2.intent_router import ConfidenceTier

    resolution = resolve_guide_intent("personel nasıl eklenir")
    assert resolution.tier is ConfidenceTier.HIGH
    assert resolution.best_guide_key == "personnel_hr_guide_add_employee"


def test_guide_question_wins_over_generic_help_intent(app, client):
    """'kpi hedef nasıl kullanılır' contains the substring 'nasıl
    kullanılır' -- conversational_intents.py's HELP pattern would otherwise
    match it (a real bug found via manual browser verification: the
    generic HELP conversational intent was checked before guide routing,
    silently swallowing every guide question ending in that exact
    phrase). Guide routing must win when a real topic is present."""
    _create_user(app, sicil_no="av2_guide_vs_help_admin", role="admin")
    _login(client, "av2_guide_vs_help_admin")

    body = _ask(client, "kpi hedef nasıl kullanılır")
    assert body["status"] == "DATA_FOUND"
    assert body["capability_key"] == "performance_mgmt_guide_kpi_targets"


def test_bare_procedural_marker_without_topic_still_gets_generic_help(app, client):
    """A genuinely topic-less 'nasıl kullanılır' must NOT be hijacked by a
    noise-level guide-vocabulary overlap (guide_intent_router's absolute
    score floor exists exactly for this case)."""
    _create_user(app, sicil_no="av2_guide_bare_help_admin", role="admin")
    _login(client, "av2_guide_bare_help_admin")

    body = _ask(client, "nasıl kullanılır")
    assert body["status"] == "CONVERSATIONAL_RESPONSE"


def test_data_query_does_not_get_hijacked_by_guide_routing():
    """'personel listele' shares the bare topic noun 'personel' with the
    add-employee guide's tags but carries no procedural ('nasıl'/'adım')
    marker -- it must resolve LOW (no guide match), not silently answer with
    procedural steps instead of routing to the real data capability."""
    from app.services.assistant_v2.guide_intent_router import resolve_guide_intent
    from app.services.assistant_v2.intent_router import ConfidenceTier

    resolution = resolve_guide_intent("personel listele")
    assert resolution.tier is ConfidenceTier.LOW
    assert resolution.best_guide_key is None


# ---------------------------------------------------------------------------
# Dispatch: authorization + numbered-step composition
# ---------------------------------------------------------------------------


def test_invoke_guide_admin_gated_guide_denies_personel_role(app):
    from app.services.assistant_v2.guide_dispatcher import invoke_guide
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    personel_id = _create_user(app, sicil_no="av2_guide_personel_denied", role="personel")
    with app.test_request_context():
        user = _get_user(app, personel_id)
        result = invoke_guide(user, "personnel_hr_guide_add_employee")
    assert result.status is AssistantResultStatus.ACCESS_DENIED


def test_invoke_guide_admin_role_allowed(app):
    from app.services.assistant_v2.guide_dispatcher import invoke_guide
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    admin_id = _create_user(app, sicil_no="av2_guide_admin_allowed", role="admin")
    with app.test_request_context():
        user = _get_user(app, admin_id)
        result = invoke_guide(user, "personnel_hr_guide_add_employee")
    assert result.status is AssistantResultStatus.DATA_FOUND
    assert isinstance(result.data, dict)
    assert result.data.get("steps")


def test_invoke_guide_unknown_key_is_capability_unavailable(app):
    from app.services.assistant_v2.guide_dispatcher import invoke_guide
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    admin_id = _create_user(app, sicil_no="av2_guide_unknown", role="admin")
    with app.test_request_context():
        user = _get_user(app, admin_id)
        result = invoke_guide(user, "does_not_exist_guide_key")
    assert result.status is AssistantResultStatus.CAPABILITY_UNAVAILABLE


def test_compose_guide_response_renders_numbered_steps(app):
    from app.services.assistant_v2.guide_dispatcher import invoke_guide
    from app.services.assistant_v2.response_composer import compose_guide_response

    admin_id = _create_user(app, sicil_no="av2_guide_compose_admin", role="admin")
    with app.test_request_context():
        user = _get_user(app, admin_id)
        result = invoke_guide(user, "support_help_guide_open_ticket")
        composed = compose_guide_response(result)
    assert "1. " in composed.answer_text
    assert "2. " in composed.answer_text


# ---------------------------------------------------------------------------
# End-to-end via the API
# ---------------------------------------------------------------------------


def test_procedural_question_via_api_returns_guide_answer_with_steps(app, client):
    _create_user(app, sicil_no="av2_guide_api_admin", role="admin")
    _login(client, "av2_guide_api_admin")

    body = _ask(client, "destek talebi nasıl açılır")
    assert body["status"] == "DATA_FOUND"
    assert "1. " in body["answer"]
    assert body["capability_key"] == "support_help_guide_open_ticket"


def test_procedural_question_via_api_denies_unauthorized_role(app, client):
    _create_user(app, sicil_no="av2_guide_api_personel", role="personel")
    _login(client, "av2_guide_api_personel")

    body = _ask(client, "personel nasıl eklenir")
    assert body["status"] == "ACCESS_DENIED"


def test_data_query_via_api_still_reaches_real_capability_not_a_guide(app, client):
    _create_user(app, sicil_no="av2_guide_api_dataquery", role="admin")
    _login(client, "av2_guide_api_dataquery")

    body = _ask(client, "personel listele")
    assert body["capability_key"] != "personnel_hr_guide_add_employee"


# ---------------------------------------------------------------------------
# Trusted related-link resolution (Phase D)
# ---------------------------------------------------------------------------


def test_resolve_related_link_returns_none_for_unknown_menu_key(app):
    from app.services.assistant_v2.related_links import resolve_related_link

    admin_id = _create_user(app, sicil_no="av2_relink_unknown", role="admin")
    with app.test_request_context():
        user = _get_user(app, admin_id)
        link = resolve_related_link(user, "this_menu_key_does_not_exist_anywhere", "Git")
    assert link is None


def test_resolve_related_link_returns_none_when_user_not_authorized(app):
    from app.services.assistant_v2.related_links import resolve_related_link

    personel_id = _create_user(app, sicil_no="av2_relink_denied", role="personel")
    with app.test_request_context():
        user = _get_user(app, personel_id)
        link = resolve_related_link(user, "admin_users", "Personel ekranına git")
    assert link is None


def test_resolve_related_link_returns_url_when_authorized(app):
    from app.services.assistant_v2.related_links import resolve_related_link

    admin_id = _create_user(app, sicil_no="av2_relink_admin", role="admin")
    with app.test_request_context():
        user = _get_user(app, admin_id)
        link = resolve_related_link(user, "admin_users", "Personel ekranına git")
    assert link is not None
    assert link["label"] == "Personel ekranına git"
    assert link["url"]


def test_guide_answer_via_api_includes_related_link_for_authorized_user(app, client):
    _create_user(app, sicil_no="av2_guide_api_relink", role="admin")
    _login(client, "av2_guide_api_relink")

    body = _ask(client, "personel nasıl eklenir")
    assert body["status"] == "DATA_FOUND"
    assert len(body["related_links"]) == 1
    assert body["related_links"][0]["url"]


# ---------------------------------------------------------------------------
# Phase R: full per-guide success/denial matrix (mirrors
# test_assistant_v2_capability_success_denial_matrix_v1.py's methodology --
# admin proves the gate opens; a dynamically-derived denial proves it closes,
# never a hardcoded role/guide assumption).
# ---------------------------------------------------------------------------


def _guide_keys():
    from app.services.assistant_v2.procedural_guides import PROCEDURAL_GUIDE_REGISTRY

    return [e.guide_key for e in PROCEDURAL_GUIDE_REGISTRY]


@pytest.fixture(scope="module")
def matrix_admin_id(app):
    return _create_user(app, sicil_no="av2_guide_matrix_admin", role="admin")


@pytest.fixture(scope="module")
def matrix_personel_id(app):
    return _create_user(app, sicil_no="av2_guide_matrix_personel", role="personel")


@pytest.mark.parametrize("guide_key", _guide_keys())
def test_guide_success_path_admin_not_denied(app, matrix_admin_id, guide_key):
    from app.services.assistant_v2.guide_dispatcher import invoke_guide
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    with app.test_request_context():
        admin = _get_user(app, matrix_admin_id)
        result = invoke_guide(admin, guide_key)
    assert result.status is not AssistantResultStatus.ACCESS_DENIED, f"{guide_key}: admin was denied"
    assert result.status is not AssistantResultStatus.CAPABILITY_UNAVAILABLE, f"{guide_key}: reported unavailable"


@pytest.mark.parametrize("guide_key", _guide_keys())
def test_guide_denial_path_dynamically_derived(app, matrix_personel_id, guide_key):
    from app.route_support import can_access_menu
    from app.services.assistant_v2.guide_dispatcher import invoke_guide
    from app.services.assistant_v2.procedural_guides import get_guide
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    entry = get_guide(guide_key)
    assert entry is not None

    with app.test_request_context():
        personel = _get_user(app, matrix_personel_id)

        if entry.required_permission is None:
            result = invoke_guide(None, guide_key)
            assert result.status is AssistantResultStatus.ACCESS_DENIED, (
                f"{guide_key}: login-only (no required_permission) guide did not deny an unauthenticated caller"
            )
            return

        personel_already_allowed = bool(can_access_menu(personel, entry.required_permission))
        if personel_already_allowed:
            result = invoke_guide(None, guide_key)
            assert result.status is AssistantResultStatus.ACCESS_DENIED, (
                f"{guide_key}: personel is genuinely authorized and an anonymous caller was ALSO not denied"
            )
        else:
            result = invoke_guide(personel, guide_key)
            assert result.status is AssistantResultStatus.ACCESS_DENIED, (
                f"{guide_key}: personel was expected to be denied (real can_access_menu check returned False) "
                f"but invoke_guide returned {result.status!r} instead"
            )


def test_every_registered_guide_is_covered_by_this_matrix():
    from app.services.assistant_v2.procedural_guides import PROCEDURAL_GUIDE_REGISTRY

    assert set(_guide_keys()) == {e.guide_key for e in PROCEDURAL_GUIDE_REGISTRY}
    assert len(_guide_keys()) == len(PROCEDURAL_GUIDE_REGISTRY)
