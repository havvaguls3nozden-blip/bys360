from __future__ import annotations

from app.services import corporate_information_center
from app.services.cic import facade, mail_service

V11_MAIL_HELPERS = {
    "_cic_v11_bool",
    "_cic_v11_clean_header",
    "_cic_v11_normalize_email",
}


def test_v11_mail_helpers_resolve_to_canonical_owner() -> None:
    for name in V11_MAIL_HELPERS:
        expected = getattr(mail_service, name)
        assert getattr(facade, name) is expected, name
        assert getattr(corporate_information_center, name) is expected, name


def test_v11_boolean_contract_is_preserved() -> None:
    truthy = (True, 1, "1", "true", "on", "yes", "evet", "tls", "ssl")
    falsy = (
        False,
        0,
        "0",
        "false",
        "off",
        "no",
        "hayir",
        "hayır",
        "none",
        "null",
    )

    for value in truthy:
        assert mail_service._cic_v11_bool(value) is True
    for value in falsy:
        assert mail_service._cic_v11_bool(value, True) is False

    assert mail_service._cic_v11_bool(None, True) is True
    assert mail_service._cic_v11_bool("", True) is True
    assert mail_service._cic_v11_bool("unknown", False) is False


def test_v11_header_cleaning_contract_is_preserved() -> None:
    assert mail_service._cic_v11_clean_header(None) == ""
    assert mail_service._cic_v11_clean_header(" A\r\nB ") == "A  B"
    assert (
        mail_service._cic_v11_clean_header("Subject\nInjected")
        == "Subject Injected"
    )


def test_v11_email_normalization_contract_is_preserved() -> None:
    normalize = mail_service._cic_v11_normalize_email
    assert normalize(" a@example.test; ") == "a@example.test"
    assert normalize("a@example.test,") == "a@example.test"
    assert normalize("bad address") == ""
    assert normalize("missing-at.example.test") == ""
    assert normalize("a@example.test\nBcc: x@test") == ""
    assert normalize(None) == ""


def test_facade_export_contract_preserves_v11_helpers() -> None:
    assert set(facade.__all__).issuperset(V11_MAIL_HELPERS)
