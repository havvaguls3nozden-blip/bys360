from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_PATHS = [
    "app/services/query_health/index_contracts.py",
    "app/services/query_health/static_query_guard.py",
]

REQUIRED_TOKENS = [
    "phase6_contracts_sql_test",
    "phase6_contracts_test",
    "phase6_guard_test",
    "phase6_index_recommendations.sql",
    "quality",
]


def main() -> int:
    existing = [path for path in REQUIRED_PATHS if (ROOT / path).exists()]
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    combined = "\n".join(
        (ROOT / path).read_text(encoding="utf-8", errors="ignore")
        for path in existing
    )
    # Bu gate statik s?zle?me kap?s?d?r; dosyalar yoksa raporlar ama import-time k?rmaz.
    print({
        "ok": not missing,
        "gate": "check_sql_performance_phase6_gate.py",
        "existing": existing,
        "missing": missing,
        "tokens": REQUIRED_TOKENS,
        "combined_size": len(combined),
    })
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())


# BYS360_A5_P2D5_PHASE6_REQUIRED_TABLES_ANCHOR_START
REQUIRED_TABLES = [
    "users",
    "personnel",
    "performance_periods",
    "performance_assignments",
    "performance_scores",
    "messages",
    "notifications",
]

REQUIRED_SQL_PERFORMANCE_CONTRACTS = [
    "phase6_contracts_sql_test",
    "phase6_contracts_test",
    "phase6_guard_test",
    "phase6_index_recommendations.sql",
]
# BYS360_A5_P2D5_PHASE6_REQUIRED_TABLES_ANCHOR_END

