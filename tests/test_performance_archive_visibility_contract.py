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
