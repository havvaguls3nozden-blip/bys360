
"""BYS360 schema guard veri tipleri.

Tüm repair modülleri bu dataclass'ı import eder.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TableRepair:
    table: str
    create_sql: str
    column_sql: tuple[str, ...] = ()
    index_sql: tuple[str, ...] = ()


