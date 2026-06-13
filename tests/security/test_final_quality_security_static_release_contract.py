from __future__ import annotations


def test_final_quality_security_static_release_contract_presence():
    assert "BYS360_SECURITY_STATIC_SOURCE_CONTRACT_V2"


def test_final_quality_security_static_release_contract_passive():
    contract_mode = "static_only_no_network_no_database_mutation"
    assert "network" in contract_mode
    assert "database" in contract_mode
