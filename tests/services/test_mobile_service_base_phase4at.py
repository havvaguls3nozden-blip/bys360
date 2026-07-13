from __future__ import annotations

from app.api.mobile.services import base as svc


def test_ok_payload_returns_base_success_contract_without_data_or_extra() -> None:
    assert svc.ok_payload() == {"ok": True}


def test_ok_payload_merges_mapping_data_and_extra_values() -> None:
    payload = svc.ok_payload({"user_id": 42, "role": "admin"}, token="abc", count=3)

    assert payload == {
        "ok": True,
        "user_id": 42,
        "role": "admin",
        "token": "abc",
        "count": 3,
    }


def test_error_payload_returns_default_error_contract_without_extra() -> None:
    assert svc.error_payload("Yetkisiz islem") == {
        "ok": False,
        "code": "mobile_error",
        "message": "Yetkisiz islem",
        "status": 400,
    }


def test_error_payload_accepts_custom_code_status_and_extra_values() -> None:
    payload = svc.error_payload(
        "Kayit bulunamadi",
        code="not_found",
        status=404,
        detail="personnel",
        retryable=False,
    )

    assert payload == {
        "ok": False,
        "code": "not_found",
        "message": "Kayit bulunamadi",
        "status": 404,
        "detail": "personnel",
        "retryable": False,
    }


def test_mobile_service_base_public_contract() -> None:
    assert svc.__name__ == "app.api.mobile.services.base"
    assert "Shared helpers for future BYS360 mobile API service extraction" in (svc.__doc__ or "")

    public_names = [name for name in dir(svc) if not name.startswith("__")]
    assert "ok_payload" in public_names
    assert "error_payload" in public_names
