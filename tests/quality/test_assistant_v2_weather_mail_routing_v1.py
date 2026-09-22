"""BYS360 Assistant V2 -- daily weather-mail intent/routing defect
(post-production live defect, narrow follow-up to the zero-arg dispatch
fix at cdefd99e).

Root cause (proven mechanically, not assumed): the underlying
`email_automation_explain_daily_weather_mail_settings` handler was already
fixed and reachable at cdefd99e -- the defect was purely in intent
ROUTING. `_score_capability()` (intent_router.py) sums, per intent_tag,
how many of a query's vocabulary-expanded tokens overlap that tag's own
expanded token set. This capability's ONLY tags before this fix were
`("email", "daily_weather_mail", "settings", "explain")`. Its sibling,
`email_automation_list_recent_mail_log`, carries the exact SAME
`"daily_weather_mail"` tag (a quasi-module-identifier, not a
distinguishing one) -- so both capabilities scored almost identically on
any weather-mail-related query, and the 0.75 close-competitor ratio
(`intent_router._MEDIUM_CONFIDENCE_RATIO`) frequently classified the pair
as tied -> MEDIUM/AMBIGUOUS instead of a clean HIGH-confidence win for the
"explain settings" capability specifically -- reproduced live via
`resolve_intent()` for all 3 reported queries before this fix (2 of the 3
resolved to MEDIUM/AMBIGUOUS, not HIGH).

Fix: added `hava`, `günlük`, `yapılandırma`, `yapılandırmasını` to this
capability's own `intent_tags` -- genuinely distinguishing Turkish
vocabulary for "weather" and "configuration" concepts no sibling
capability shares. Deliberately did NOT add `durum` or `göster` (both
tried and mechanically proven, via a live probe against a battery of
unrelated queries, to be broad enough to hijack unrelated queries like
"İzin durumumu göster" and "Performans dönemimi göster" once added as
standalone tags) -- excluded per this mandate's own explicit caution
against broad words. `email_automation_list_recent_mail_log`'s own tags
were not touched.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.ci_safe

_PASSWORD = "Assist_v2_Test_Pw_1!"

_LIVE_QUERIES = (
    "Günlük hava durumu e-posta ayarlarını açıkla",
    "Günlük hava durumu e-posta ayarlarını göster",
    "Hava durumu e-posta yapılandırmasını göster",
)

_UNRELATED_QUERIES = (
    "İzin durumumu göster",
    "Performans dönemimi göster",
    "Anket sonuçlarını göster",
    "Duyuruları göster",
    "AI Governance ayarlarını açıkla",
    "Dosya Merkezi'nde kota durumumu nasıl görebilirim?",
)


def _mk_user(db, User, *, sicil_no, role):
    existing = User.query.filter_by(sicil_no=sicil_no).first()
    if existing is not None:
        return existing
    user = User(
        sicil_no=sicil_no, email=f"{sicil_no}@ktb.gov.tr", ad="Weather", soyad="Routing",
        role=role, is_active=True, must_change_password=False, must_set_security_question=False,
    )
    user.set_password(_PASSWORD)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin(app):
    from app.extensions import db
    from app.models import User

    with app.app_context():
        yield _mk_user(db, User, sicil_no="weather_routing_admin", role="admin")


@pytest.fixture
def personel(app):
    from app.extensions import db
    from app.models import User

    with app.app_context():
        yield _mk_user(db, User, sicil_no="weather_routing_personel", role="personel")


# ---------------------------------------------------------------------------
# Routing: all 3 live queries resolve to the correct capability
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("query", _LIVE_QUERIES)
def test_live_query_routes_to_weather_mail_settings(query):
    from app.services.assistant_v2.intent_router import ConfidenceTier, resolve_intent

    resolution = resolve_intent(query)
    assert resolution.tier is ConfidenceTier.HIGH, (query, resolution.tier, resolution.candidates)
    assert resolution.best_capability_key == "email_automation_explain_daily_weather_mail_settings"


@pytest.mark.parametrize("query", _LIVE_QUERIES)
def test_live_query_end_to_end_via_service_authorized_returns_data_found(app, admin, query):
    from app.services.assistant_v2.result_contract import AssistantResultStatus
    from app.services.assistant_v2.service import AssistantV2Service

    with app.app_context(), app.test_request_context():
        answer = AssistantV2Service().ask(admin, query)
    assert answer.status == AssistantResultStatus.DATA_FOUND.value
    assert answer.capability_key == "email_automation_explain_daily_weather_mail_settings"


@pytest.mark.parametrize("query", _LIVE_QUERIES)
def test_live_query_no_generic_out_of_scope_fallback(app, admin, query):
    from app.services.assistant_v2.service import AssistantV2Service

    with app.app_context(), app.test_request_context():
        answer = AssistantV2Service().ask(admin, query)
    assert answer.status not in {"OUT_OF_SCOPE", "AMBIGUOUS_REQUEST"}


# ---------------------------------------------------------------------------
# Authorization unchanged
# ---------------------------------------------------------------------------


def test_authorized_caller_returns_data_found(app, admin):
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    with app.app_context():
        result = invoke_capability(admin, "email_automation_explain_daily_weather_mail_settings")
    assert result.status is AssistantResultStatus.DATA_FOUND


def test_unauthorized_caller_remains_access_denied(app, personel):
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    with app.app_context():
        result = invoke_capability(personel, "email_automation_explain_daily_weather_mail_settings")
    assert result.status is AssistantResultStatus.ACCESS_DENIED


# ---------------------------------------------------------------------------
# No unrelated-query hijack (mandate's own explicit caution)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("query", _UNRELATED_QUERIES)
def test_unrelated_queries_not_hijacked_by_weather_mail_settings(query):
    from app.services.assistant_v2.intent_router import resolve_intent

    resolution = resolve_intent(query)
    assert resolution.best_capability_key != "email_automation_explain_daily_weather_mail_settings", (
        query, resolution.tier, resolution.candidates
    )


def test_sibling_capability_intent_tags_unchanged():
    """email_automation_list_recent_mail_log's own tags must not have been
    touched by this fix."""
    from app.services.assistant_v2.capability_registry import get_capability

    entry = get_capability("email_automation_list_recent_mail_log")
    assert entry is not None
    assert entry.intent_tags == ("email", "daily_weather_mail", "log", "list")


# ---------------------------------------------------------------------------
# safety_classifier.py: the real, deeper root cause -- a substring-based
# OUT_OF_SCOPE hint ("hava durumu") rejected these queries BEFORE intent
# routing ever ran. Fixed with a narrow, explicit co-occurrence exception
# for that one hint only. Genuine weather chit-chat and every other hint
# must remain unaffected.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query",
    (
        "Bugün hava durumu nasıl?",
        "İstanbul hava durumu",
        "Yarın hava durumu ne olacak",
        "Hava durumu",
    ),
)
def test_genuine_weather_chitchat_still_out_of_scope(query):
    from app.services.assistant_v2.safety_classifier import SafetyCategory, classify

    result = classify(query)
    assert result.category is SafetyCategory.OUT_OF_SCOPE
    assert result.matched_rule == "hava durumu"


@pytest.mark.parametrize(
    "query,expected_hint",
    (
        ("Dolar kuru ne kadar", "dolar"),
        ("Bugün borsa nasıl", "borsa"),
        ("Son dakika haberler", "haber"),
        ("Futbol maçı ne zaman", "futbol"),
    ),
)
def test_other_out_of_scope_hints_unaffected(query, expected_hint):
    from app.services.assistant_v2.safety_classifier import SafetyCategory, classify

    result = classify(query)
    assert result.category is SafetyCategory.OUT_OF_SCOPE
    assert result.matched_rule == expected_hint
