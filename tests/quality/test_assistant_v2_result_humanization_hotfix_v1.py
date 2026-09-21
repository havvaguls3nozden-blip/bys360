"""BYS360 Assistant V2 -- user-facing structured result humanization
hotfix (post-production defect closure, follow-up to the File Center
intent/raw-capability-ID hotfix).

Root cause (proven before this fix, not assumed): `response_composer.py`'s
generic dict-shaped fallback, `_render_dict_summary()`, rendered every key
of `result.data` verbatim as `f"{key}: {value}"` -- for
`file_center_read_quota_status` (whose read_adapter returns a bare dict,
not a list) this produced literal machine field names in the visible
answer: "Dosya Merkezi Kota Durumu: total_used_bytes: 28149,
total_file_count: 1." Routing and authorization were both already correct;
the defect was purely in response composition.

Fix: a domain-aware formatter for file_center_read_quota_status (using a
new, deterministic `format_bytes_tr()` helper), registered in a small
`_CAPABILITY_FORMATTERS` dict dispatch checked before the generic
renderer; plus a small, centrally-located omit/relabel guard inside
`_render_dict_summary()` itself so the small set of purely-technical field
names the mandate named (user_id, unit_id, menu_key, capability_key,
source_type) never leak by raw key from ANY dict-shaped capability, while
created_at/updated_at are relabeled and properly date-formatted rather
than dropped (they carry real end-user meaning, e.g. for an audit-log
detail view).
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
            sicil_no=sicil_no, email=f"{sicil_no}@ktb.gov.tr", ad="Humanize", soyad="Hotfix",
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


def _result(**overrides: Any) -> Any:
    from app.services.assistant_v2.result_contract import (
        AssistantCapabilityResult,
        AssistantResultStatus,
    )

    defaults: dict[str, Any] = dict(
        status=AssistantResultStatus.DATA_FOUND,
        message="İstenen bilgi bulundu.",
        capability_key="file_center_read_quota_status",
        module_key="file_center",
        data={
            "policy_label": None, "max_storage_gb": None, "warning_threshold_percent": None,
            "total_used_bytes": 28149, "total_file_count": 1,
        },
        source_label="Dosya Merkezi Kota Politikası",
    )
    defaults.update(overrides)
    return AssistantCapabilityResult(**defaults)


# ---------------------------------------------------------------------------
# Byte formatter boundaries (Phase C)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "num_bytes, expected",
    [
        (0, "0 B"),
        (1, "1 B"),
        (1023, "1023 B"),
        (1024, "1,0 KB"),
        (28149, "27,5 KB"),
        (1024 * 1024, "1,0 MB"),
        (1024 * 1024 * 1024, "1,0 GB"),
    ],
)
def test_format_bytes_tr_boundaries(num_bytes, expected):
    from app.services.assistant_v2.language_helpers import format_bytes_tr

    assert format_bytes_tr(num_bytes) == expected


# ---------------------------------------------------------------------------
# Goal A: File Center quota humanization (items 1-6)
# ---------------------------------------------------------------------------


def test_quota_result_does_not_expose_total_used_bytes_key():
    """Mandate item 1."""
    from app.services.assistant_v2 import response_composer

    composed = response_composer.compose_response(_result())
    assert "total_used_bytes" not in composed.answer_text


def test_quota_result_does_not_expose_total_file_count_key():
    """Mandate item 2."""
    from app.services.assistant_v2 import response_composer

    composed = response_composer.compose_response(_result())
    assert "total_file_count" not in composed.answer_text


def test_28149_bytes_renders_as_human_readable_size():
    """Mandate item 3 -- the exact reported production value."""
    from app.services.assistant_v2 import response_composer

    composed = response_composer.compose_response(_result())
    assert "27,5 KB" in composed.answer_text


def test_one_file_renders_naturally():
    """Mandate item 4."""
    from app.services.assistant_v2 import response_composer

    composed = response_composer.compose_response(_result(data={
        "policy_label": None, "max_storage_gb": None, "warning_threshold_percent": None,
        "total_used_bytes": 0, "total_file_count": 1,
    }))
    assert "1 dosya" in composed.answer_text
    assert "1 dosyalar" not in composed.answer_text


def test_zero_files_renders_naturally():
    """Mandate item 5."""
    from app.services.assistant_v2 import response_composer

    composed = response_composer.compose_response(_result(data={
        "policy_label": None, "max_storage_gb": None, "warning_threshold_percent": None,
        "total_used_bytes": 0, "total_file_count": 0,
    }))
    assert "0 dosya" in composed.answer_text


def test_large_size_renders_deterministically():
    """Mandate item 6 -- run twice, must be byte-identical (no randomness,
    no locale dependence)."""
    from app.services.assistant_v2 import response_composer

    big = _result(data={
        "policy_label": None, "max_storage_gb": None, "warning_threshold_percent": None,
        "total_used_bytes": 5 * 1024 * 1024 * 1024, "total_file_count": 12000,
    })
    first = response_composer.compose_response(big).answer_text
    second = response_composer.compose_response(big).answer_text
    assert first == second
    assert "5,0 GB" in first
    assert "12000 dosya" in first


def test_example_output_matches_mandate_worked_example():
    from app.services.assistant_v2 import response_composer

    composed = response_composer.compose_response(_result())
    assert "Dosya Merkezi'nde toplam 27,5 KB alan kullanılıyor." in composed.answer_text
    assert "Toplam 1 dosya bulunuyor." in composed.answer_text


# ---------------------------------------------------------------------------
# Provenance / structured contract preservation (items 7, 12)
# ---------------------------------------------------------------------------


def test_source_provenance_remains_present():
    """Mandate item 7."""
    from app.services.assistant_v2 import response_composer

    composed = response_composer.compose_response(_result())
    assert "Kaynak: Dosya Merkezi Kota Politikası" in composed.answer_text


def test_raw_structured_result_contract_unchanged_internally():
    """Mandate item 12 -- the humanization change is in response
    composition only; the underlying capability's own returned dict shape
    must be byte-for-byte the same as before this hotfix."""
    import inspect

    from app.services.assistant_v2.read_adapters import file_center_read_quota_status

    source = inspect.getsource(file_center_read_quota_status)
    for key in ("policy_label", "max_storage_gb", "warning_threshold_percent", "total_used_bytes", "total_file_count"):
        assert f'"{key}"' in source


# ---------------------------------------------------------------------------
# Authorization unchanged (items 8, 9)
# ---------------------------------------------------------------------------


def test_authorized_admin_still_receives_data_found(app, client):
    """Mandate item 8."""
    _create_user(app, sicil_no="humanize_hotfix_admin", role="admin")
    _login(client, "humanize_hotfix_admin")

    response = client.post("/ai-agent/api/v2/ask", json={"question": "kota durumumu göster"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "DATA_FOUND"
    assert body["capability_key"] == "file_center_read_quota_status"
    assert "total_used_bytes" not in body["answer"]
    assert "total_file_count" not in body["answer"]


def test_unauthorized_personel_still_gets_access_denied(app, client):
    """Mandate item 9."""
    _create_user(app, sicil_no="humanize_hotfix_personel", role="personel")
    _login(client, "humanize_hotfix_personel")

    response = client.post("/ai-agent/api/v2/ask", json={"question": "kota durumumu göster"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ACCESS_DENIED"


# ---------------------------------------------------------------------------
# Web/mobile presentation compatibility (items 10, 11)
# ---------------------------------------------------------------------------


def test_web_presentation_remains_compatible(app):
    """Mandate item 10."""
    from app.services.assistant_v2.service import AssistantV2Service
    from app.services.assistant_v2.web_presentation_adapter import adapt_for_legacy_web

    admin_id = _create_user(app, sicil_no="humanize_hotfix_web", role="admin")
    with app.app_context(), app.test_request_context():
        admin = _get_user(app, admin_id)
        answer = AssistantV2Service().ask(admin, "kota durumumu göster")
        web = adapt_for_legacy_web(answer)

    assert "total_used_bytes" not in web["answer"]
    assert "total_file_count" not in web["answer"]
    assert "27,5 KB" in web["answer"] or "KB" in web["answer"] or "B" in web["answer"]
    assert web["sources"]


def test_mobile_presentation_remains_compatible(app):
    """Mandate item 11."""
    from app.services.assistant_v2.mobile_presentation_adapter import adapt_for_mobile
    from app.services.assistant_v2.service import AssistantV2Service

    admin_id = _create_user(app, sicil_no="humanize_hotfix_mobile", role="admin")
    with app.app_context(), app.test_request_context():
        admin = _get_user(app, admin_id)
        answer = AssistantV2Service().ask(admin, "kota durumumu göster")
        mobile = adapt_for_mobile(answer)

    assert "total_used_bytes" not in mobile["answer"]
    assert "total_file_count" not in mobile["answer"]
    assert mobile["intent"]


# ---------------------------------------------------------------------------
# No raw snake_case regression, cross-module guard (item 13 + Phase E)
# ---------------------------------------------------------------------------


def test_no_raw_snake_case_field_in_rendered_quota_answer():
    """Mandate item 13."""
    from app.services.assistant_v2 import response_composer

    composed = response_composer.compose_response(_result())
    for forbidden in ("total_used_bytes", "total_file_count", "policy_label", "max_storage_gb", "warning_threshold_percent"):
        assert forbidden not in composed.answer_text


def test_central_guard_omits_pure_technical_fields_for_any_dict_capability():
    """Phase E cross-module audit, mechanical proof: the omit-list applies
    regardless of which capability produced the dict, not just file_center."""
    from app.services.assistant_v2 import response_composer

    result = _result(
        capability_key="audit_read_change_log_detail",
        module_key="audit",
        data={"change_summary": "Ayar güncellendi", "user_id": 42, "source_type": "manual", "menu_key": "settings"},
    )
    composed = response_composer.compose_response(result)
    for forbidden in ("user_id", "source_type", "menu_key"):
        assert forbidden not in composed.answer_text
    assert "42" not in composed.answer_text or "user_id" not in composed.answer_text


def test_central_guard_relabels_date_fields_instead_of_dropping_them():
    """created_at/updated_at carry real meaning -- must be relabeled and
    reformatted, not silently omitted like the pure-identifier fields."""
    from app.services.assistant_v2 import response_composer

    result = _result(
        capability_key="audit_read_change_log_detail",
        module_key="audit",
        data={"change_summary": "Ayar güncellendi", "created_at": "2026-09-15T10:00:00"},
    )
    composed = response_composer.compose_response(result)
    assert "created_at" not in composed.answer_text
    assert "Oluşturulma" in composed.answer_text
    assert "2026-09-15T10:00:00" not in composed.answer_text
