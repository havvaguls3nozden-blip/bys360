# BYS360_MOBILE_SERVICE_SCAFFOLD_P1_2_V2_17_7
"""Shared helpers for future BYS360 mobile API service extraction.

P1.2 only creates the service foundation. Route functions remain in their current
files until P1.3+ micro-refactor packages move them one group at a time.
"""
from __future__ import annotations

from typing import Any
from collections.abc import Mapping


def ok_payload(data: Mapping[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": True}
    if data:
        payload.update(dict(data))
    if extra:
        payload.update(extra)
    return payload


def error_payload(message: str, *, code: str = "mobile_error", status: int = 400, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": False, "code": code, "message": message, "status": status}
    if extra:
        payload.update(extra)
    return payload
