"""BYS360 SP-1F Yetkinlik Kutuphanesi servis yardimcilari.
Bu servis ham karar uretmez; yetkinlik kutuphanesi ve rol sablonlarini kurumsal gorunume hazirlar.
"""
from __future__ import annotations

from typing import Any


def normalize_competency_status(active: bool | None) -> str:
    return "Aktif" if active is not False else "Pasif"


def build_competency_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    active = sum(1 for r in rows if r.get("active", True) is not False)
    categories = sorted({r.get("competency_category") or r.get("category") or "Genel" for r in rows})
    return {"total": total, "active": active, "category_count": len(categories), "categories": categories}
