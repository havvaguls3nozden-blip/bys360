from __future__ import annotations

import ast
from pathlib import Path

from app.services import corporate_information_center
from app.services.cic import facade, mail_service, repository

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_PATH = ROOT / "app/services/cic/repository.py"

V11_MAIL_HELPERS = {
    "_cic_v11_bool",
    "_cic_v11_clean_header",
    "_cic_v11_normalize_email",
}


def _repository_definitions() -> set[str]:
    tree = ast.parse(REPOSITORY_PATH.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_repository_no_longer_defines_v11_mail_helper_duplicates() -> None:
    assert _repository_definitions().isdisjoint(V11_MAIL_HELPERS)


def test_v11_mail_helpers_resolve_to_canonical_owner() -> None:
    for name in V11_MAIL_HELPERS:
        expected = getattr(mail_service, name)
        assert getattr(repository, name) is expected, name
        assert getattr(facade, name) is expected, name
        assert getattr(corporate_information_center, name) is expected, name


def test_v11_boolean_contract_is_preserved() -> None:
    truthy = (True, 1, "1", "true", "on", "yes", "evet", "tls", "ssl")
    falsy = (False, 0, "0", "false", "off", "no", "hayir", "hayır", "none", "null")

    for value in truthy:
        assert repository._cic_v11_bool(value) is True
    for value in falsy:
        assert repository._cic_v11_bool(value, True) is False

    assert repository._cic_v11_bool(None, True) is True
    assert repository._cic_v11_bool("", True) is True
    assert repository._cic_v11_bool("unknown", False) is False


def test_v11_header_cleaning_contract_is_preserved() -> None:
    assert repository._cic_v11_clean_header(None) == ""
    assert repository._cic_v11_clean_header(" A\r\nB ") == "A  B"
    assert repository._cic_v11_clean_header("Subject\nInjected") == "Subject Injected"


def test_v11_email_normalization_contract_is_preserved() -> None:
    assert repository._cic_v11_normalize_email(" a@example.test; ") == "a@example.test"
    assert repository._cic_v11_normalize_email("a@example.test,") == "a@example.test"
    assert repository._cic_v11_normalize_email("bad address") == ""
    assert repository._cic_v11_normalize_email("missing-at.example.test") == ""
    assert repository._cic_v11_normalize_email("a@example.test\nBcc: x@test") == ""
    assert repository._cic_v11_normalize_email(None) == ""


def test_repository_star_export_contract_does_not_expand() -> None:
    assert "_cic_v11_bool" in repository.__all__
    assert "_cic_v11_clean_header" in repository.__all__
    assert "_cic_v11_normalize_email" not in repository.__all__
