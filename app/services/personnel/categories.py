# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
"""BYS360 personel kategori servisleri.

Faz 2 kalıcı sözleşme:
- Varsayılan kategori seti tek yerden gelir.
- Eski users.personnel_category metin alanı ile users.performance_category_id FK alanı birlikte yürütülür.
- Rapor/karne tarafı kişi detayı sızdırmadan kategori eşleştirmesi yapar.
"""

from typing import Any

PERSONNEL_CATEGORY_DEFAULTS: tuple[str, ...] = (
    "Güvenlik",
    "Temizlik",
    "İdari Personel",
    "Teknik Personel",
    "Deneme Süreli Personel",
    "Diğer",
)
PERSONNEL_CATEGORY_OPTIONS = PERSONNEL_CATEGORY_DEFAULTS
DEFAULT_PERSONNEL_CATEGORIES = PERSONNEL_CATEGORY_DEFAULTS
PERSONNEL_CATEGORY_DEFAULT_LABELS = PERSONNEL_CATEGORY_DEFAULTS
BYS360_PERFORMANCE_COMPLETION_PHASE2_PERSONNEL_CATEGORY_SERVICE = True


def normalize_personnel_category_label(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "Diğer"
    aliases = {
        "guvenlik": "Güvenlik",
        "güvenlik": "Güvenlik",
        "temizlik": "Temizlik",
        "idari": "İdari Personel",
        "idari personel": "İdari Personel",
        "ıdari personel": "İdari Personel",
        "teknik": "Teknik Personel",
        "teknik personel": "Teknik Personel",
        "deneme": "Deneme Süreli Personel",
        "deneme sureli personel": "Deneme Süreli Personel",
        "deneme süreli personel": "Deneme Süreli Personel",
        "diger": "Diğer",
        "diğer": "Diğer",
    }
    lookup = {item.casefold(): item for item in PERSONNEL_CATEGORY_DEFAULTS}
    return aliases.get(text.casefold(), lookup.get(text.casefold(), text[:80]))


def slugify_personnel_category(value: Any) -> str:
    import re

    text = normalize_personnel_category_label(value).lower()
    for old, new in {"ğ": "g", "ü": "u", "ş": "s", "ı": "i", "ö": "o", "ç": "c", "İ": "i", "Ğ": "g", "Ü": "u", "Ş": "s", "Ö": "o", "Ç": "c"}.items():
        text = text.replace(old, new)
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_") or "diger"


def _session_bind(db_session: Any):
    if db_session is None:
        return None
    try:
        return db_session.get_bind()
    except Exception:
        return getattr(db_session, "bind", None)


def _table_available(db_session: Any, table_name: str = "personnel_categories") -> bool:
    try:
        from sqlalchemy import inspect

        bind = _session_bind(db_session)
        return bool(bind is not None and inspect(bind).has_table(table_name))
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return False


def get_personnel_category_options(db_session: Any | None = None) -> list[str]:
    if db_session is not None and _table_available(db_session):
        try:
            from app.models import PersonnelCategory

            rows = (
                db_session.query(PersonnelCategory)
                .filter(PersonnelCategory.is_active.is_(True))
                .order_by(PersonnelCategory.sort_order.asc(), PersonnelCategory.name.asc())
                .all()
            )
            labels = [normalize_personnel_category_label(getattr(row, "name", None)) for row in rows if getattr(row, "name", None)]
            if labels:
                return labels
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/personnel/categories.py")
    return list(PERSONNEL_CATEGORY_DEFAULTS)


def ensure_personnel_category(db_session: Any, label: Any):
    label = normalize_personnel_category_label(label)
    if db_session is None or not _table_available(db_session):
        return None
    try:
        from app.models import PersonnelCategory

        row = db_session.query(PersonnelCategory).filter(PersonnelCategory.name == label).first()
        if row:
            if getattr(row, "is_active", True) is False:
                row.is_active = True
            return row
        sort_order = (PERSONNEL_CATEGORY_DEFAULTS.index(label) + 1) * 10 if label in PERSONNEL_CATEGORY_DEFAULTS else 999
        row = PersonnelCategory(
            name=label,
            code=slugify_personnel_category(label),
            description=f"{label} personel performans kategori grubu",
            sort_order=sort_order,
            is_active=True,
        )
        db_session.add(row)
        db_session.flush()
        return row
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return None


def seed_default_personnel_categories(db_session: Any) -> list[str]:
    labels: list[str] = []
    for label in PERSONNEL_CATEGORY_DEFAULTS:
        ensure_personnel_category(db_session, label)
        labels.append(label)
    return labels


def assign_user_performance_category(user: Any, category_label: Any, *, db_session: Any | None = None) -> str:
    label = normalize_personnel_category_label(category_label)
    if hasattr(user, "personnel_category"):
        user.personnel_category = label
    if db_session is not None and hasattr(user, "performance_category_id"):
        row = ensure_personnel_category(db_session, label)
        if row is not None:
            user.performance_category_id = getattr(row, "id", None)
    return label


def get_user_personnel_category_label(user: Any) -> str:
    if user is None:
        return "Diğer"
    related = getattr(user, "performance_category", None)
    if related is not None and getattr(related, "name", None):
        return normalize_personnel_category_label(getattr(related, "name"))
    return normalize_personnel_category_label(getattr(user, "personnel_category", None))


def user_matches_personnel_category(user: Any, category_label: Any) -> bool:
    return get_user_personnel_category_label(user) == normalize_personnel_category_label(category_label)


__all__ = [
    "PERSONNEL_CATEGORY_DEFAULTS",
    "PERSONNEL_CATEGORY_OPTIONS",
    "DEFAULT_PERSONNEL_CATEGORIES",
    "PERSONNEL_CATEGORY_DEFAULT_LABELS",
    "normalize_personnel_category_label",
    "slugify_personnel_category",
    "get_personnel_category_options",
    "ensure_personnel_category",
    "seed_default_personnel_categories",
    "assign_user_performance_category",
    "get_user_personnel_category_label",
    "user_matches_personnel_category",
]
