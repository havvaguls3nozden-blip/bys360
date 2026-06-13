from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def test_performance_common_preserves_manager_chain_core_fields() -> None:
    source = read("app/services/performance/common.py")

    required_tokens = [
        "class ManagerChain",
        "manager_1_id",
        "manager_2_id",
        "manager_3_id",
        "manager_1_name",
        "manager_2_name",
        "manager_3_name",
        "level_3_enabled",
        "level_3_scoring_enabled",
        "is_single_manager_case",
        "effective_weights",
        "info_notes",
        "warnings",
        "issues",
    ]

    missing = [token for token in required_tokens if token not in source]
    assert not missing, "Eksik ManagerChain ortak alanı: " + ", ".join(missing)


def test_performance_common_preserves_role_and_unit_normalization_contract() -> None:
    source = read("app/services/performance/common.py")

    required_tokens = [
        "TR_CHAR_MAP",
        "PRESIDENT_ROLE_KEYS",
        "PRESIDENT_TITLE_KEYS",
        "HUKUK_UNIT_KEYS",
        "HUKUK_TITLE_KEYS",
        "THIRD_MANAGER_STANDARD_KEY",
        "THIRD_MANAGER_HEADER_ALIASES",
        "fetch_active_non_admin_users",
        "build_assignment_due_date",
        "get_period",
    ]

    missing = [token for token in required_tokens if token not in source]
    assert not missing, "Eksik common servis sözleşme izi: " + ", ".join(missing)
