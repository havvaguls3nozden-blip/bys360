"""BYS360 Assistant V2 -- File Center quota intent + raw-capability-ID UI
guard hotfix (post-production defect closure).

Root cause (proven empirically before this fix, not assumed):
1. `domain_vocabulary._SUFFIXES` had no Turkish 1st-person possessive
   suffix ("-m", "-mı/-mi/-mu/-mü"), so "kotam"/"kotamı" never reduced to
   the bare "kota" the "quota" tag's canonical-form bridge expands to --
   these queries scored zero extra points for the quota capability.
2. Even when "kota" matched literally, `file_center_read_quota_status`'s
   only distinguishing tag was the single word "quota" (1 point), while
   the generic "file_center"/"dosya"/"merkezi" overlap shared by ALL THREE
   file_center capabilities was worth 3 points -- close enough to trip
   `_MEDIUM_CONFIDENCE_RATIO` into a 3-way AMBIGUOUS_REQUEST tie instead of
   a clear HIGH-confidence single match.
3. `web_presentation_adapter.py` and `mobile_presentation_adapter.py` both
   rendered `clarification["candidates"]` (raw capability_key strings)
   directly as `suggested_questions` chip text -- exposing internal
   identifiers like "file_center_read_quota_status" to real users.

Fix: added the missing possessive suffixes + a "storage"<->"depolama"
canonical bridge (domain_vocabulary.py, module-agnostic); widened
`file_center_read_quota_status`'s own intent_tags with "kota"/"depolama"
(capability_registry.py, data-only change); added a `suggestion_label`
field + a single `resolve_suggestion_label()` helper capability_registry.py
that both presentation adapters now call instead of reading
`clarification["candidates"]` raw.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.ci_safe

_PASSWORD = "Assist_v2_Test_Pw_1!"

_QUOTA_PHRASES = (
    "Dosya Merkezi'nde kota durumumu nasıl görebilirim?",
    "kota durumumu göster",
    "dosya kotam ne kadar?",
    "ne kadar kotam kaldı?",
    "Dosya Merkezi kotamı göster",
    "depolama kotam nedir?",
    "kota kullanımımı göster",
)


def _create_user(app, *, sicil_no, role, password=_PASSWORD):
    from app.extensions import db
    from app.models import User

    with app.app_context():
        existing = User.query.filter_by(sicil_no=sicil_no).first()
        if existing is not None:
            return existing.id
        user = User(
            sicil_no=sicil_no, email=f"{sicil_no}@ktb.gov.tr", ad="FC", soyad="Hotfix",
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


# ---------------------------------------------------------------------------
# Goal A: deterministic quota intent (items 1-3)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("phrase", _QUOTA_PHRASES)
def test_quota_phrase_resolves_to_high_confidence_quota_capability(phrase):
    from app.services.assistant_v2.intent_router import ConfidenceTier, resolve_intent

    resolution = resolve_intent(phrase)
    assert resolution.tier is ConfidenceTier.HIGH, (phrase, resolution.tier, resolution.candidates)
    assert resolution.best_capability_key == "file_center_read_quota_status"


def test_dosya_merkezinde_kota_durumumu_nasil_gorebilirim_resolves(app):
    """Mandate item 1 -- the exact reported production defect phrase,
    proven end-to-end through AssistantV2Service.ask(), not just the
    intent router in isolation."""
    from app.services.assistant_v2.result_contract import AssistantResultStatus
    from app.services.assistant_v2.service import AssistantV2Service

    admin_id = _create_user(app, sicil_no="fc_hotfix_q1", role="admin")
    with app.app_context(), app.test_request_context():
        admin = _get_user(app, admin_id)
        answer = AssistantV2Service().ask(admin, "Dosya Merkezi'nde kota durumumu nasıl görebilirim?")
    assert answer.status == AssistantResultStatus.DATA_FOUND.value
    assert answer.capability_key == "file_center_read_quota_status"


def test_kota_durumumu_goster_resolves(app):
    """Mandate item 2."""
    from app.services.assistant_v2.result_contract import AssistantResultStatus
    from app.services.assistant_v2.service import AssistantV2Service

    admin_id = _create_user(app, sicil_no="fc_hotfix_q2", role="admin")
    with app.app_context(), app.test_request_context():
        admin = _get_user(app, admin_id)
        answer = AssistantV2Service().ask(admin, "kota durumumu göster")
    assert answer.status == AssistantResultStatus.DATA_FOUND.value
    assert answer.capability_key == "file_center_read_quota_status"


def test_dosya_kotam_ne_kadar_resolves(app):
    """Mandate item 3."""
    from app.services.assistant_v2.result_contract import AssistantResultStatus
    from app.services.assistant_v2.service import AssistantV2Service

    admin_id = _create_user(app, sicil_no="fc_hotfix_q3", role="admin")
    with app.app_context(), app.test_request_context():
        admin = _get_user(app, admin_id)
        answer = AssistantV2Service().ask(admin, "dosya kotam ne kadar?")
    assert answer.status == AssistantResultStatus.DATA_FOUND.value
    assert answer.capability_key == "file_center_read_quota_status"


# ---------------------------------------------------------------------------
# Goal B/C: no raw capability IDs, broad request gets friendly choices
# (items 4-6)
# ---------------------------------------------------------------------------


def test_broad_file_center_request_does_not_expose_raw_capability_ids(app):
    """Mandate item 4. A genuinely ambiguous broad request (three
    file_center capabilities legitimately tie) must still never leak raw
    identifiers -- it should present friendly, human-readable choices."""
    from app.services.assistant_v2.result_contract import AssistantResultStatus
    from app.services.assistant_v2.service import AssistantV2Service
    from app.services.assistant_v2.web_presentation_adapter import adapt_for_legacy_web

    admin_id = _create_user(app, sicil_no="fc_hotfix_broad", role="admin")
    with app.app_context(), app.test_request_context():
        admin = _get_user(app, admin_id)
        answer = AssistantV2Service().ask(admin, "Dosya Merkezi hakkında bilgi almak istiyorum")
        web = adapt_for_legacy_web(answer)

    assert answer.status == AssistantResultStatus.AMBIGUOUS_REQUEST.value
    assert "file_center_read_quota_status" not in answer.answer
    for label in web["suggested_questions"]:
        assert not label.startswith("file_center_"), label


def test_ambiguous_request_suggestions_use_human_facing_labels(app):
    """Mandate item 5 -- the suggestions are genuinely readable Turkish
    phrases, not just "anything that isn't the raw key"."""
    from app.services.assistant_v2.service import AssistantV2Service
    from app.services.assistant_v2.web_presentation_adapter import adapt_for_legacy_web

    admin_id = _create_user(app, sicil_no="fc_hotfix_labels", role="admin")
    with app.app_context(), app.test_request_context():
        admin = _get_user(app, admin_id)
        answer = AssistantV2Service().ask(admin, "Dosya Merkezi hakkında bilgi almak istiyorum")
        web = adapt_for_legacy_web(answer)

    assert "Kota durumumu göster" in web["suggested_questions"]
    assert "Son güvenlik taramalarını göster" in web["suggested_questions"]
    assert "Dosya Merkezi yetkilerini açıkla" in web["suggested_questions"]


def test_no_raw_file_center_identifier_in_rendered_answer_or_suggestions_any_adapter(app):
    """Mandate item 6, covering BOTH presentation adapters (web and
    mobile) -- the defect existed in both."""
    from app.services.assistant_v2.mobile_presentation_adapter import adapt_for_mobile
    from app.services.assistant_v2.service import AssistantV2Service
    from app.services.assistant_v2.web_presentation_adapter import adapt_for_legacy_web

    admin_id = _create_user(app, sicil_no="fc_hotfix_both_adapters", role="admin")
    with app.app_context(), app.test_request_context():
        admin = _get_user(app, admin_id)
        answer = AssistantV2Service().ask(admin, "Dosya Merkezi hakkında bilgi almak istiyorum")
        web = adapt_for_legacy_web(answer)
        mobile = adapt_for_mobile(answer)

    assert not answer.answer.strip().startswith("file_center_")
    for label in list(web["suggested_questions"]) + list(mobile["suggested_questions"]):
        assert not label.startswith("file_center_"), label
        assert "_" not in label or " " in label, f"looks like a raw identifier, not a phrase: {label!r}"


# ---------------------------------------------------------------------------
# Authorization must not change (items 7-9)
# ---------------------------------------------------------------------------


def test_authorized_admin_still_reaches_quota_capability(app, client):
    """Mandate item 7, through the real HTTP endpoint end-to-end."""
    _create_user(app, sicil_no="fc_hotfix_authz_admin", role="admin")
    _login(client, "fc_hotfix_authz_admin")

    response = client.post("/ai-agent/api/v2/ask", json={"question": "kota durumumu göster"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "DATA_FOUND"
    assert body["capability_key"] == "file_center_read_quota_status"


def test_unauthorized_personel_still_gets_access_denied(app, client):
    """Mandate item 8 -- the hotfix must not widen who can reach this
    capability. file_center_read_quota_status is gated by
    can_manage_file_center_settings (admin-like only), unaffected by the
    intent-routing/label changes."""
    _create_user(app, sicil_no="fc_hotfix_authz_personel", role="personel")
    _login(client, "fc_hotfix_authz_personel")

    response = client.post("/ai-agent/api/v2/ask", json={"question": "kota durumumu göster"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ACCESS_DENIED"


def test_no_permission_widening_capability_registry_unchanged(app):
    """Mandate item 9 -- the fix touched intent_tags/suggestion_label
    only; permission_key, is_self_describing, and the auth_override
    string on all three file_center capabilities must be byte-identical
    to before this hotfix."""
    from app.services.assistant_v2.capability_registry import get_capability

    expected_auth_override = "app.file_center.permissions.can_manage_file_center_settings"
    for key in (
        "file_center_read_quota_status",
        "file_center_list_recent_security_scans",
        "file_center_explain_role_matrix",
    ):
        entry = get_capability(key)
        assert entry is not None
        assert entry.permission_key is None
        assert entry.is_self_describing is False
        assert entry.extra.get("auth_override") == expected_auth_override


# ---------------------------------------------------------------------------
# Defensive: resolve_suggestion_label never leaks a raw key, even for an
# unknown capability_key (should be unreachable in practice, but proven).
# ---------------------------------------------------------------------------


def test_resolve_suggestion_label_never_returns_raw_key_even_for_unknown_capability():
    from app.services.assistant_v2.capability_registry import resolve_suggestion_label

    label = resolve_suggestion_label("totally_unknown_capability_key_xyz")
    assert label != "totally_unknown_capability_key_xyz"
    assert "_" not in label
