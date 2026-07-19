from __future__ import annotations

from types import SimpleNamespace

from app.services.performance.completion_phase3_visibility_scope import (
    access_denied_context,
    build_visibility_profile,
    category_average_visibility_payload,
    phase3_can_open_performance_reports,
    phase3_can_view_category_average,
    phase3_can_view_employee,
    resolve_visibility_role_key,
)


def _user(role: str, user_id: int = 1, **extra):
    payload = {"id": user_id, "role": role, "is_authenticated": True, "is_admin": False, "is_superuser": False}
    payload.update(extra)
    return SimpleNamespace(**payload)


def test_personnel_visibility_is_own_record_only():
    actor = _user("personel", 10)
    assert resolve_visibility_role_key(actor) == "personel"
    assert build_visibility_profile(actor).own_record_only is True
    assert phase3_can_view_employee(actor, 10) is True
    assert phase3_can_view_employee(actor, 11) is False
    assert phase3_can_open_performance_reports(actor) is False


def test_manager_roles_are_scope_limited_not_personnel_detail_for_all():
    coordinator = _user("koordinator", 20)
    group_head = _user("grup_baskani", 30)
    assert build_visibility_profile(coordinator).scope_limited is True
    assert build_visibility_profile(group_head).scope_limited is True
    assert phase3_can_open_performance_reports(coordinator) is True
    assert phase3_can_open_performance_reports(group_head) is True


def test_president_and_admin_have_global_visibility_profile():
    president = _user("baskan", 40)
    admin = _user("admin", 50, is_admin=True)
    assert build_visibility_profile(president).can_view_global is True
    assert build_visibility_profile(admin).can_view_global is True


def test_category_average_privacy_for_personnel():
    actor = _user("personel", 60)
    assert phase3_can_view_category_average(actor, include_person_details=False) is True
    assert phase3_can_view_category_average(actor, include_person_details=True) is False
    payload = category_average_visibility_payload(actor)
    assert payload["can_view_average"] is True
    assert payload["can_view_person_details"] is False


def test_corporate_access_denied_context():
    ctx = access_denied_context()
    assert ctx["access_denied"] is True
    assert "yetkiniz" in ctx["message"].lower()
