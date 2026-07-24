"""Central SQL identifier validation and quoting policy for BYS360."""

from __future__ import annotations

import re
from collections.abc import Collection

from sqlalchemy.engine import Dialect

_SQL_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*$"
)


def validate_sql_identifier(
    value: str,
    *,
    allowed: Collection[str] | None = None,
) -> str:
    """Validate one unqualified SQL identifier and an optional allowlist."""

    if (
        not isinstance(value, str)
        or not _SQL_IDENTIFIER_PATTERN.fullmatch(value)
    ):
        raise ValueError("Unsafe SQL identifier.")

    if allowed is not None and value not in allowed:
        raise ValueError(
            "SQL identifier is outside the allowed set."
        )

    return value


def quote_sql_identifier(
    value: str,
    *,
    dialect: Dialect,
    allowed: Collection[str] | None = None,
) -> str:
    """Validate and quote an SQL identifier with the active dialect."""

    safe_value = validate_sql_identifier(
        value,
        allowed=allowed,
    )
    return dialect.identifier_preparer.quote(safe_value)
