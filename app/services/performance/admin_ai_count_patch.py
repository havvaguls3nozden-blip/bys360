from __future__ import annotations

from collections.abc import Iterable
from typing import Any

"""Performans kapsamı sayaç yardımcıları.

Bu dosya önce top-level patch parçası olarak ``rows`` ve ``users`` değişkenlerini
oluşmadan kullanıyordu. V2 ile güvenli helper modülüne dönüştürüldü.
"""

try:
    from app.services.performance.common import is_performance_scope_user
except Exception:  # pragma: no cover
    def is_performance_scope_user(user: Any) -> bool:
        return True


def filter_performance_scope_rows(rows: Iterable[Any]) -> list[Any]:
    return [row for row in rows if is_performance_scope_user(getattr(row, "user", row))]


def filter_performance_scope_users(users: Iterable[Any]) -> list[Any]:
    return [user for user in users if is_performance_scope_user(user)]
