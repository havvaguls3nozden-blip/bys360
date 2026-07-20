"""BYS360 Maintenance 10E - Geçmiş karne arşivi görünürlük sözleşmesi."""
from __future__ import annotations

from types import SimpleNamespace


def _user(user_id=1, role="personel", **extra):
    payload = {"id": user_id, "role": role, "is_authenticated": True, "is_admin": False, "is_superuser": False}
    payload.update(extra)
    return SimpleNamespace(**payload)


def test_archive_personnel_only_contract():
    from app.services.performance import archive_service as svc

    user = _user(42, "personel")
    assert svc.is_personnel_only_archive_user(user) is True
    assert svc.allowed_archive_employee_ids(user) == {42}


def test_archive_manager_empty_scope_never_means_everyone(monkeypatch):
    from app.services.performance import archive_service as svc

    manager = _user(7, "koordinatör")
    monkeypatch.setattr(svc, "phase3_allowed_employee_ids", lambda user: set())

    assert svc.is_manager_archive_user(manager) is True
    # Boş kapsam herkese açılmaz; güvenli daraltma kendi ID'sine düşer.
    assert svc.allowed_archive_employee_ids(manager) == {7}


def test_archive_direct_detail_access_uses_allowed_ids(monkeypatch):
    from app.services.performance import archive_service as svc

    personel = _user(10, "personel")
    record = SimpleNamespace(employee_id=11)
    own_record = SimpleNamespace(employee_id=10)

    assert svc.can_view_archived_result(personel, record) is False
    assert svc.can_view_archived_result(personel, own_record) is True


def test_phase7_archive_policy_keeps_group_heads_scope_limited():
    from app.services.performance.phase7_scorecard_archive_policy import (
        resolve_archive_visibility,
    )

    for role in (
        "grup baskani",
        "grup_baskani",
        "grup başkanı",
        "personel_ve_destek_hizmetleri_grup_baskani",
    ):
        in_scope = resolve_archive_visibility(
            viewer=_user(7, role),
            employee_id=11,
            scope_employee_ids=[11, 12],
        )
        assert in_scope.allowed is True
        assert in_scope.scope == "scope"
        assert in_scope.can_view_source_document is False

        out_of_scope = resolve_archive_visibility(
            viewer=_user(7, role),
            employee_id=99,
            scope_employee_ids=[11, 12],
        )
        assert out_of_scope.allowed is False
        assert out_of_scope.scope == "denied"
        assert out_of_scope.can_view_source_document is False

    for role in (
        "baskan",
        "baskan_yardimcisi",
        "Admin",
        "SİSTEM_YÖNETİCİSİ",
    ):
        global_view = resolve_archive_visibility(
            viewer=_user(7, role),
            employee_id=99,
            scope_employee_ids=[],
        )
        assert global_view.allowed is True
        assert global_view.scope == "all"
        assert global_view.can_view_source_document is True

    similar_title = resolve_archive_visibility(
        viewer=_user(7, "baskan_danismani"),
        employee_id=99,
        scope_employee_ids=[],
    )
    assert similar_title.allowed is False
    assert similar_title.scope == "denied"
    assert similar_title.can_view_source_document is False
