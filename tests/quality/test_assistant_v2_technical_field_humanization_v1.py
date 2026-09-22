"""BYS360 Assistant V2 -- post-release structured field humanization,
cross-module technical field cleanup (follow-up to the result-humanization
hotfix, 261ad674).

Root cause (proven by mechanical trace + live checks before this fix, not
assumed): `response_composer._render_dict_summary()`'s generic fallback
rendered every non-omitted key of a dict-shaped `result.data` verbatim as
`f"{key}: {value}"`. This mandate's own audit found two distinct problem
classes beyond the narrow set already fixed in the prior hotfix:

1. Several READ_RECORD capabilities carry raw internal identifiers/enum
   codes with real end-user meaning only once translated: author_user_id,
   actor_user_id, target_user_id, target_role_name, module_key,
   scheduler_key, link_url, announcement_type, notification_type, plus
   several booleans (is_read, results_published, captcha_enabled,
   login_force_captcha_for_unknown_user) that were rendered as raw Python
   True/False, and two more raw ISO datetimes (publish_start_at/
   publish_end_at/closed_at) alongside the already-fixed created_at/
   updated_at.
2. Several existing, REUSED service functions (not read_adapters.py) can
   return a NESTED dict/list, or even a live SQLAlchemy ORM instance
   (`app.services.home_dashboard_service.build_home_summary_context`'s
   `active_period`, confirmed live via a direct call in this same audit --
   that function is written for Jinja template rendering, not JSON/prose
   safety). The old generic renderer had no defense against this at all;
   `f"{key}: {value}"` on an ORM object would render its Python repr into
   the user-facing answer.

Fix: (a) additive human-readable sibling fields
(author_name/actor_name/target_user_name/target_role_label/
announcement_type_label/notification_type_label) resolved in
read_adapters.py from data the SAME already-authorized query already
loads (no new cross-user lookup, no invented translation -- every mapping
reused is an EXISTING one already used elsewhere in this codebase:
Announcement.type_label, NOTIFICATION_TYPE_LABELS, ROLE_CHOICES); (b) a
widened central omit/relabel guard in response_composer.py
(_OMITTED_TECHNICAL_FIELDS, _RELABELED_DATE_FIELDS,
_RELABELED_PLAIN_FIELDS) plus a UNIVERSAL bool -> Evet/Hayır conversion
for every dict-shaped capability's boolean fields; (c) a general,
capability-agnostic safety net that only ever prose-renders the five
JSON-primitive-safe Python types (str/int/float/bool/None) -- any nested
dict/list/tuple/set or arbitrary object (including a raw ORM instance) is
silently skipped from the flat prose dump. `result.data` itself is
completely unchanged in every case; only prose composition changed.

One field named in this mandate's own "known deferred candidates" list
turned out to be a FALSE POSITIVE on mechanical trace, not a real leak:
file_center_explain_role_matrix's `role_key`. That capability returns a
LIST of dicts, which response_composer renders through
`_render_list_like()` -- a function that only ever extracts a per-row
LABEL via `_extract_item_label()`'s fixed field-name priority list, which
already includes `role_label` (ahead of `role_key`, which is not in that
list at all) -- so `role_key` was never actually reachable from user-
facing prose, before or after this fix. Proven below, not just asserted.
"""
from __future__ import annotations

from typing import Any

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
            sicil_no=sicil_no, email=f"{sicil_no}@ktb.gov.tr", ad="TechField", soyad="Hotfix",
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


def _result(*, capability_key: str, module_key: str, data: Any, source_label: str = "Test Kaynağı") -> Any:
    from app.services.assistant_v2.result_contract import (
        AssistantCapabilityResult,
        AssistantResultStatus,
    )

    return AssistantCapabilityResult(
        status=AssistantResultStatus.DATA_FOUND,
        message="İstenen bilgi bulundu.",
        capability_key=capability_key,
        module_key=module_key,
        data=data,
        source_label=source_label,
    )


def _compose(*, capability_key: str, module_key: str, data: Any) -> str:
    from app.services.assistant_v2 import response_composer

    return response_composer.compose_response(_result(capability_key=capability_key, module_key=module_key, data=data)).answer_text


# ---------------------------------------------------------------------------
# Items 1-3: raw user-identifying ids never exposed
# ---------------------------------------------------------------------------


def test_author_user_id_not_exposed():
    """Mandate item 1."""
    text = _compose(
        capability_key="portal_read_post_detail", module_key="portal",
        data={"id": 5, "title": "Duyuru", "body": "İçerik", "post_type": "normal", "status": "published",
              "published_at": "2026-09-01T10:00:00", "author_user_id": 42, "author_name": "Ayşe Yılmaz"},
    )
    assert "author_user_id" not in text
    assert "42" not in text
    assert "Ayşe Yılmaz" in text


def test_actor_user_id_not_exposed():
    """Mandate item 2."""
    text = _compose(
        capability_key="audit_read_change_log_detail", module_key="audit",
        data={"id": 1, "change_scope": "settings", "action_type": "update", "summary": "Ayar güncellendi",
              "actor_user_id": 7, "actor_name": "Mehmet Demir", "target_user_id": None, "target_user_name": None,
              "target_role_name": None, "target_role_label": None, "is_rollback": False},
    )
    assert "actor_user_id" not in text
    assert "Mehmet Demir" in text


def test_target_user_id_not_exposed():
    """Mandate item 3."""
    text = _compose(
        capability_key="audit_read_change_log_detail", module_key="audit",
        data={"id": 1, "change_scope": "settings", "action_type": "role_change", "summary": "Rol değiştirildi",
              "actor_user_id": 7, "actor_name": "Mehmet Demir", "target_user_id": 99, "target_user_name": "Zeynep Kaya",
              "target_role_name": "personel", "target_role_label": "Personel", "is_rollback": False},
    )
    assert "target_user_id" not in text
    assert "99" not in text
    assert "Zeynep Kaya" in text
    assert "target_role_name" not in text
    assert "Personel" in text


# ---------------------------------------------------------------------------
# Items 4-5: internal keys never exposed when a human label exists
# ---------------------------------------------------------------------------


def test_module_key_not_exposed():
    """Mandate item 4."""
    text = _compose(
        capability_key="dashboard_explain_module", module_key="dashboard",
        data={"module_key": "dashboard", "display_name": "Ana Panel", "description": "Ana panel modülü.",
              "widget_visibility_note": "Widget görünürlüğü şu an kod içinde sabittir."},
    )
    assert "module_key" not in text
    assert "Ana Panel" in text or "widget_visibility_note" not in text  # display_name still readable as generic key:value


def test_role_key_not_exposed_file_center_role_matrix_false_positive_confirmed():
    """Mandate item 5 -- also the mechanical false-positive proof: this is
    a LIST-shaped capability, rendered by _render_list_like(), which never
    reads role_key at all (only role_label, via _LABEL_FIELD_PRIORITY)."""
    from app.services.assistant_v2 import response_composer

    data = [
        {"role_key": "admin", "role_label": "Yönetici", "can_upload_files": True, "can_download_files": True,
         "can_create_guest_links": True, "can_manage_settings": True, "can_manage_security": True},
        {"role_key": "personel", "role_label": "Personel", "can_upload_files": True, "can_download_files": True,
         "can_create_guest_links": False, "can_manage_settings": False, "can_manage_security": False},
    ]
    composed = response_composer.compose_response(
        _result(capability_key="file_center_explain_role_matrix", module_key="file_center", data=data)
    )
    assert "role_key" not in composed.answer_text
    assert "Yönetici" in composed.answer_text
    assert "Personel" in composed.answer_text


# ---------------------------------------------------------------------------
# Items 6-8: raw enum-ish fields not exposed by name
# ---------------------------------------------------------------------------


def test_raw_notification_type_not_exposed():
    """Mandate item 6."""
    text = _compose(
        capability_key="notifications_read_notification_detail", module_key="notifications",
        data={"id": 3, "title": "Yeni yorum", "body": "Gönderinize yorum yapıldı.",
              "notification_type": "portal_comment_mention", "notification_type_label": "Genel",
              "priority": "normal", "is_read": False, "link_url": "/portal/feed#post-5",
              "created_at": "2026-09-10T08:00:00"},
    )
    assert "notification_type" not in text.replace("notification_type_label", "")
    assert "portal_comment_mention" not in text
    assert "link_url" not in text
    assert "/portal/feed#post-5" not in text


def test_raw_announcement_type_not_exposed():
    """Mandate item 7."""
    text = _compose(
        capability_key="communication_read_announcement_detail", module_key="communication",
        data={"id": 1, "title": "Bakım Duyurusu", "body": "Sistem bakımda olacaktır.",
              "announcement_type": "maintenance", "announcement_type_label": "Bakım",
              "publish_start_at": "2026-09-15T09:00:00", "publish_end_at": "2026-09-16T18:00:00"},
    )
    assert "announcement_type:" not in text
    assert "maintenance" not in text
    assert "Bakım" in text


def test_raw_period_type_key_not_exposed():
    """Mandate item 8 -- the raw snake_case KEY must not appear; the value
    itself (already stored as end-user Turkish text by the real period
    create/edit screens -- confirmed against app/templates/period_edit.html
    -- or a legacy internal code from older data) is passed through as-is
    rather than guessing an unverifiable translation, per this mandate's
    own "do not invent translations for unknown values" rule."""
    text = _compose(
        capability_key="performance_mgmt_read_period_summary", module_key="performance_mgmt",
        data={"id": 4, "title": "2026 Yıllık Dönem", "period_type": "Yıllık", "start_date": "2026-01-01",
              "end_date": "2026-12-31", "is_active": True, "results_published": False, "evaluation_count": 12},
    )
    assert "period_type" not in text
    assert "Dönem Türü: Yıllık" in text


# ---------------------------------------------------------------------------
# Item 9: no raw True/False for user-facing booleans, universally
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value,expected", [(True, "Evet"), (False, "Hayır")])
def test_no_raw_true_false_for_any_dict_capability_boolean(value, expected):
    """Mandate item 9 -- proven for a capability with NO explicit key-label
    entry at all, showing the universal bool->Evet/Hayır conversion is not
    limited to the named fields."""
    text = _compose(
        capability_key="audit_read_change_log_detail", module_key="audit",
        data={"id": 1, "change_scope": "settings", "action_type": "update", "summary": "Değişiklik",
              "is_rollback": value},
    )
    assert "True" not in text and "False" not in text
    assert expected in text


# ---------------------------------------------------------------------------
# Items 10-12: dates humanized
# ---------------------------------------------------------------------------


def test_publish_start_at_humanized():
    """Mandate item 10."""
    text = _compose(
        capability_key="communication_read_announcement_detail", module_key="communication",
        data={"id": 1, "title": "Duyuru", "body": "İçerik", "announcement_type": "info",
              "announcement_type_label": "Bilgilendirme", "publish_start_at": "2026-09-15T09:00:00", "publish_end_at": None},
    )
    assert "publish_start_at" not in text
    assert "2026-09-15T09:00:00" not in text
    assert "Yayın Başlangıcı: 15 Eylül 2026" in text


def test_publish_end_at_humanized():
    """Mandate item 11."""
    text = _compose(
        capability_key="communication_read_announcement_detail", module_key="communication",
        data={"id": 1, "title": "Duyuru", "body": "İçerik", "announcement_type": "info",
              "announcement_type_label": "Bilgilendirme", "publish_start_at": None, "publish_end_at": "2026-09-20T18:00:00"},
    )
    assert "publish_end_at" not in text
    assert "2026-09-20T18:00:00" not in text
    assert "Yayın Bitişi: 20 Eylül 2026" in text


def test_closed_at_humanized():
    """Mandate item 12."""
    text = _compose(
        capability_key="support_help_read_ticket_detail", module_key="support_help",
        data={"id": 9, "ticket_no": "T-9", "title": "Destek talebi", "description": "Açıklama",
              "status": "closed", "priority": "normal", "created_at": "2026-09-01T10:00:00",
              "closed_at": "2026-09-05T12:00:00"},
    )
    assert "closed_at" not in text
    assert "2026-09-05T12:00:00" not in text
    assert "Kapanma: 5 Eylül 2026" in text


# ---------------------------------------------------------------------------
# Items 13-15: policy/state booleans human-readable
# ---------------------------------------------------------------------------


def test_captcha_policy_human_readable():
    """Mandate item 13."""
    text = _compose(
        capability_key="security_session_read_captcha_policy", module_key="security_session",
        data={"captcha_enabled": True, "login_force_captcha_for_unknown_user": False},
    )
    assert "captcha_enabled" not in text
    assert "login_force_captcha_for_unknown_user" not in text
    assert "True" not in text and "False" not in text
    assert "CAPTCHA Etkin: Evet" in text
    assert "Bilinmeyen Kullanıcı İçin CAPTCHA Zorunlu: Hayır" in text


def test_notification_read_state_human_readable():
    """Mandate item 14."""
    text = _compose(
        capability_key="notifications_read_notification_detail", module_key="notifications",
        data={"id": 3, "title": "Bildirim", "body": "İçerik", "notification_type": "system",
              "notification_type_label": "Sistem", "priority": "normal", "is_read": True,
              "link_url": None, "created_at": "2026-09-10T08:00:00"},
    )
    assert "is_read" not in text
    assert "True" not in text
    assert "Okunma Durumu: Evet" in text


def test_performance_results_published_human_readable():
    """Mandate item 15."""
    text = _compose(
        capability_key="performance_mgmt_read_period_summary", module_key="performance_mgmt",
        data={"id": 4, "title": "2026 Dönemi", "period_type": "Yıllık", "is_active": True,
              "results_published": True, "evaluation_count": 8},
    )
    assert "results_published" not in text
    assert "True" not in text
    assert "Sonuçlar Yayınlandı: Evet" in text


# ---------------------------------------------------------------------------
# Items 16-17: structured contract + provenance preserved
# ---------------------------------------------------------------------------


def test_structured_result_data_remains_intact_for_every_touched_adapter():
    """Mandate item 16 -- every raw field this wave's read_adapters.py
    changes touched must still be present in the adapter's own source (all
    changes here are additive human-readable siblings, nothing removed)."""
    import inspect

    from app.services.assistant_v2 import read_adapters

    expectations = {
        read_adapters.portal_read_post_detail: ("author_user_id", "author_name"),
        read_adapters.communication_read_announcement_detail: ("announcement_type", "announcement_type_label"),
        read_adapters.notifications_read_notification_detail: ("notification_type", "notification_type_label", "is_read", "link_url"),
        read_adapters.audit_read_change_log_detail: (
            "actor_user_id", "actor_name", "target_user_id", "target_user_name",
            "target_role_name", "target_role_label",
        ),
    }
    for fn, expected_keys in expectations.items():
        source = inspect.getsource(fn)
        for key in expected_keys:
            assert f'"{key}"' in source, (fn.__name__, key)


def test_provenance_remains_present():
    """Mandate item 17."""
    text = _compose(
        capability_key="audit_read_change_log_detail", module_key="audit",
        data={"id": 1, "change_scope": "settings", "action_type": "update", "summary": "Değişiklik"},
    )
    assert "Kaynak: Test Kaynağı" in text


# ---------------------------------------------------------------------------
# Items 18-19: authorization unchanged, ACCESS_DENIED fail-closed
# ---------------------------------------------------------------------------


def test_authorization_unchanged_for_every_touched_capability():
    """Mandate item 18 -- this wave touched response composition and
    read_adapters.py's RETURNED FIELDS only; permission_key/
    is_self_describing/auth_override on every touched capability must be
    byte-identical to before this wave."""
    from app.services.assistant_v2.capability_registry import get_capability

    expected = {
        "portal_read_post_detail": ("portal_feed", False, None),
        "communication_read_announcement_detail": ("announcements", False, None),
        "notifications_read_notification_detail": ("notifications", False, None),
        "audit_read_change_log_detail": ("settings", False, None),
        "dashboard_explain_module": ("dashboard", False, None),
        "performance_mgmt_read_period_summary": ("performance_reports", False, None),
        "support_help_read_ticket_detail": ("support_my_tickets", False, None),
        "security_session_read_captcha_policy": ("settings_center_security", False, None),
        "file_center_explain_role_matrix": (None, False, "app.file_center.permissions.can_manage_file_center_settings"),
        "scheduled_jobs_read_feedback_followup_status": ("settings_center_scheduled_jobs", False, None),
    }
    for key, (permission_key, is_self_describing, auth_override) in expected.items():
        entry = get_capability(key)
        assert entry is not None, key
        assert entry.permission_key == permission_key, key
        assert entry.is_self_describing is is_self_describing, key
        assert entry.extra.get("auth_override") == auth_override, key


def test_access_denied_remains_fail_closed_for_touched_capability(app, client):
    """Mandate item 19, through the real HTTP endpoint end-to-end, for a
    capability this wave actually touched (audit change-log detail is
    admin-only via 'settings')."""
    _create_user(app, sicil_no="techfield_denied_personel", role="personel")
    _login(client, "techfield_denied_personel")

    response = client.post("/ai-agent/api/v2/ask", json={"question": "ayar değişiklik kaydı detayını göster"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] in {"ACCESS_DENIED", "AMBIGUOUS_REQUEST", "NO_DATA", "CAPABILITY_UNAVAILABLE"}
    assert body["status"] != "DATA_FOUND"


# ---------------------------------------------------------------------------
# Items 20-21: web/mobile presentation compatibility
# ---------------------------------------------------------------------------


def test_web_presentation_compatible_for_notification_detail(app):
    """Mandate item 20."""
    from app.services.assistant_v2 import response_composer
    from app.services.assistant_v2.web_presentation_adapter import adapt_for_legacy_web

    with app.app_context(), app.test_request_context():
        composed = response_composer.compose_response(
            _result(
                capability_key="notifications_read_notification_detail", module_key="notifications",
                data={"id": 3, "title": "Bildirim", "body": "İçerik", "notification_type": "system",
                      "notification_type_label": "Sistem", "priority": "normal", "is_read": False,
                      "link_url": "/bildirimler", "created_at": "2026-09-10T08:00:00"},
            )
        )

        class _FakeAnswer:
            status = "DATA_FOUND"
            answer = composed.answer_text
            module_keys = ("notifications",)
            capability_key = "notifications_read_notification_detail"
            sources = ()
            conversation_id = None
            clarification = None
            related_links = ()

        web = adapt_for_legacy_web(_FakeAnswer())
    assert "notification_type" not in web["answer"]
    assert "is_read" not in web["answer"]
    assert "link_url" not in web["answer"]


def test_mobile_presentation_compatible_for_audit_detail(app):
    """Mandate item 21."""
    from app.services.assistant_v2 import response_composer
    from app.services.assistant_v2.mobile_presentation_adapter import adapt_for_mobile

    with app.app_context(), app.test_request_context():
        composed = response_composer.compose_response(
            _result(
                capability_key="audit_read_change_log_detail", module_key="audit",
                data={"id": 1, "change_scope": "settings", "action_type": "update", "summary": "Değişiklik",
                      "actor_user_id": 7, "actor_name": "Mehmet Demir"},
            )
        )

        class _FakeAnswer:
            status = "DATA_FOUND"
            answer = composed.answer_text
            module_keys = ("audit",)
            capability_key = "audit_read_change_log_detail"
            related_links = ()
            clarification = None

        mobile = adapt_for_mobile(_FakeAnswer())
    assert "actor_user_id" not in mobile["answer"]
    assert "Mehmet Demir" in mobile["answer"]


# ---------------------------------------------------------------------------
# Items 22-23: no regression on the previous hotfix's own behavior
# ---------------------------------------------------------------------------


def test_previous_file_center_quota_humanization_still_passes():
    """Mandate item 22."""
    text = _compose(
        capability_key="file_center_read_quota_status", module_key="file_center",
        data={"policy_label": None, "max_storage_gb": None, "warning_threshold_percent": None,
              "total_used_bytes": 28149, "total_file_count": 1},
    )
    assert "total_used_bytes" not in text
    assert "27,5 KB" in text


def test_previous_friendly_capability_labels_still_pass():
    """Mandate item 23."""
    from app.services.assistant_v2.capability_registry import resolve_suggestion_label

    assert resolve_suggestion_label("file_center_read_quota_status") == "Kota durumumu göster"


# ---------------------------------------------------------------------------
# Item 24: unknown structured field fallback remains safe
# ---------------------------------------------------------------------------


def test_unknown_structured_field_fallback_remains_safe():
    """Mandate item 24 -- a field this wave never named must still render
    plainly (not omitted, not crashing) via the untouched generic path."""
    text = _compose(
        capability_key="settings_auth_summarize_role_permission_coverage", module_key="settings_auth",
        data={"totally_unseen_future_field": "some value"},
    )
    assert "totally_unseen_future_field: some value" in text


def test_nested_and_orm_object_values_never_leak_raw_repr():
    """Extra proof (Phase A re-audit finding, dashboard_summarize_my_home_context):
    a raw SQLAlchemy-model-shaped value (simulated here without a DB round
    trip) and a nested dict/list must never be dumped as a Python repr into
    the answer -- the generic renderer must silently skip them, not crash
    or leak internal structure."""

    class _FakeOrmObject:
        def __repr__(self):
            return "<PerformancePeriod id=2 title=Some Period active=True>"

    text = _compose(
        capability_key="dashboard_summarize_my_home_context", module_key="dashboard",
        data={
            "today_label": "22.09.2026", "pending_tasks": 3, "unread_notifications": 1,
            "active_period": _FakeOrmObject(),
            "nested_ignore_me": {"a": 1, "b": [1, 2, 3]},
        },
    )
    assert "PerformancePeriod" not in text
    assert "active_period" not in text
    assert "nested_ignore_me" not in text
    assert "pending_tasks: 3" in text


def test_recipient_user_id_list_never_leaks_raw_ids():
    """Extra proof (Phase A re-audit finding,
    email_automation_explain_daily_weather_mail_settings): a raw list of
    internal user ids must never be flattened into the answer."""
    text = _compose(
        capability_key="email_automation_explain_daily_weather_mail_settings", module_key="email_automation",
        data={"enabled": True, "city": "Ankara", "recipient_user_ids": [3, 17, 42], "last_result": {"ok": True}},
    )
    assert "recipient_user_ids" not in text
    assert "17" not in text
    assert "last_result" not in text
    assert "Etkin: Evet" in text


# ---------------------------------------------------------------------------
# Item 25: comprehensive no-raw-snake-case-leak sweep across every
# capability this wave touched
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "capability_key,module_key,data,forbidden",
    [
        (
            "portal_read_post_detail", "portal",
            {"id": 1, "title": "T", "body": "B", "post_type": "normal", "status": "published",
             "published_at": None, "author_user_id": 1, "author_name": "A"},
            ("author_user_id",),
        ),
        (
            "communication_read_announcement_detail", "communication",
            {"id": 1, "title": "T", "body": "B", "announcement_type": "warning",
             "announcement_type_label": "Uyarı", "publish_start_at": None, "publish_end_at": None},
            ("announcement_type:",),
        ),
        (
            "notifications_read_notification_detail", "notifications",
            {"id": 1, "title": "T", "body": "B", "notification_type": "survey_assigned",
             "notification_type_label": "Genel", "priority": "normal", "is_read": False,
             "link_url": "/x", "created_at": None},
            ("notification_type:", "link_url", "is_read:"),
        ),
        (
            "scheduled_jobs_read_feedback_followup_status", "scheduled_jobs",
            {"scheduler_key": "feedback_followup", "env_var": "BYS360_FEEDBACK_FOLLOWUP_SCHEDULER",
             "raw_value": "true", "enabled": True},
            ("scheduler_key",),
        ),
        (
            "audit_read_change_log_detail", "audit",
            {"id": 1, "change_scope": "s", "action_type": "a", "summary": "s",
             "actor_user_id": 1, "actor_name": "A", "target_user_id": 2, "target_user_name": "B",
             "target_role_name": "personel", "target_role_label": "Personel", "is_rollback": False},
            ("actor_user_id", "target_user_id", "target_role_name"),
        ),
    ],
)
def test_no_raw_snake_case_field_leaks_in_covered_responses(capability_key, module_key, data, forbidden):
    """Mandate item 25."""
    text = _compose(capability_key=capability_key, module_key=module_key, data=data)
    for forbidden_field in forbidden:
        assert forbidden_field not in text, (capability_key, forbidden_field, text)
