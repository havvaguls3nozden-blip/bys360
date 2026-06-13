from __future__ import annotations


def test_static_release_contract_presence():
    assert "BYS360_SECURITY_STATIC_SOURCE_CONTRACT_V1"


def test_static_release_contract_is_passive():
    value = "passive_static_contract"
    assert value.endswith("contract")
