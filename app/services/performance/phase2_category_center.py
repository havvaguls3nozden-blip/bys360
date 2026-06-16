# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
"""BYS360 Performans Tamamlama Faz 2 kategori merkezi.

Amaç:
- Personel/grup kategorilerini tek sözleşmede toplamak.
- Personel kartı, import ve rapor filtrelerinin aynı kategori listesini kullanmasını sağlamak.
- Kategori ortalamasını kişi detayı göstermeden üretmek.

Bu servis DB hazır değilken de güvenli varsayılanlarla çalışır; canlı DB işlemleri
migration ve repair scriptleriyle ayrıca güvenceye alınır.
"""

from dataclasses import dataclass
from typing import Any, Iterable
logger = logging.getLogger(__name__)

PHASE2_CATEGORY_CENTER_VERSION = "performance-completion-phase2-category-center-v1"
BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_CENTER = True

DEFAULT_CATEGORY_ROWS: tuple[tuple[str, str, int], ...] = (
    ("guvenlik", "Güvenlik", 10),
    ("temizlik", "Temizlik", 20),
    ("idari_personel", "İdari Personel", 30),
    ("teknik_personel", "Teknik Personel", 40),
    ("deneme_sureli_personel", "Deneme Süreli Personel", 50),
    ("diger", "Diğer", 60),
)

DEFAULT_CATEGORY_LABELS: tuple[str, ...] = tuple(row[1] for row in DEFAULT_CATEGORY_ROWS)
PRIVACY_NOTE = "Kategori ortalaması kişi detayı göstermeden hesaplanır; kişi detayı gösterilmez."

PHASE2_SETTING_ROWS: tuple[tuple[str, str, str, str, str, str], ...] = (
    (
        "performance_categories",
        "categories_enabled",
        "Personel kategori altyapısı aktif",
        "bool",
        "True",
        "Güvenlik, Temizlik, İdari Personel, Teknik Personel, Deneme Süreli Personel ve Diğer kategorilerini performans süreçlerinde etkin tutar.",
    ),
    (
        "performance_categories",
        "personnel_card_category_required",
        "Personel kartında kategori alanı zorunlu",
        "bool",
        "True",
        "Personel ekleme/düzenleme ekranlarında kategori alanının kurumsal veri olarak tutulmasını sağlar.",
    ),
    (
        "performance_categories",
        "import_category_column_enabled",
        "Toplu personel import kategori sütununu desteklesin",
        "bool",
        "True",
        "Excel/toplu aktarımda kategori/personel kategorisi sütunlarının okunmasını sağlar.",
    ),
    (
        "performance_reporting",
        "category_filter_enabled",
        "Performans raporlarında kategori filtresi aktif",
        "bool",
        "True",
        "Raporlarda personel/grup kategorisine göre filtreleme yapılmasını sağlar.",
    ),
    (
        "performance_reporting",
        "category_average_privacy_no_detail",
        "Kategori ortalaması kişi detayı göstermeden hesaplansın",
        "bool",
        "True",
        "Personel yalnızca kendi kategori ortalamasını görür; kategori içindeki kişi detayları gösterilmez.",
    ),
)


@dataclass(frozen=True)
class CategoryAverageSummary:
    category_label: str
    average_score: float
    count: int
    detail_visible: bool = False
    person_detail_visible: bool = False
    privacy_note: str = PRIVACY_NOTE

    def as_dict(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "available": self.count > 0,
            "category_label": self.category_label,
            "selected_category": self.category_label,
            "average_score": self.average_score,
            "category_average": self.average_score,
            "average": self.average_score,
            "count": self.count,
            "sample_count": self.count,
            "detail_visible": self.detail_visible,
            "person_detail_visible": self.person_detail_visible,
            "privacy_note": self.privacy_note,
        }


def normalize_category_label(value: Any) -> str:
    try:
        from app.services.personnel.categories import normalize_personnel_category_label

        return normalize_personnel_category_label(value)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
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
        lookup = {label.casefold(): label for label in DEFAULT_CATEGORY_LABELS}
        return aliases.get(text.casefold(), lookup.get(text.casefold(), text[:80]))


def slugify_category(value: Any) -> str:
    try:
        from app.services.personnel.categories import slugify_personnel_category

        return slugify_personnel_category(value)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        import re

        text = normalize_category_label(value).lower()
        for old, new in {"ğ": "g", "ü": "u", "ş": "s", "ı": "i", "ö": "o", "ç": "c", "İ": "i"}.items():
            text = text.replace(old, new)
        return re.sub(r"[^a-z0-9]+", "_", text).strip("_") or "diger"


def get_category_options(db_session: Any | None = None) -> list[str]:
    try:
        from app.services.personnel.categories import get_personnel_category_options

        return list(get_personnel_category_options(db_session))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return list(DEFAULT_CATEGORY_LABELS)


def ensure_category(db_session: Any, label: Any):
    try:
        from app.services.personnel.categories import ensure_personnel_category

        return ensure_personnel_category(db_session, label)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None


def seed_default_categories(db_session: Any) -> list[str]:
    labels: list[str] = []
    for _code, label, _order in DEFAULT_CATEGORY_ROWS:
        row = ensure_category(db_session, label)
        if row is not None or db_session is None:
            labels.append(label)
    return labels or list(DEFAULT_CATEGORY_LABELS)


def assign_user_category(user: Any, category_label: Any, *, db_session: Any | None = None) -> str:
    label = normalize_category_label(category_label)
    try:
        from app.services.personnel.categories import assign_user_performance_category

        return assign_user_performance_category(user, label, db_session=db_session)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        if hasattr(user, "personnel_category"):
            user.personnel_category = label
        return label


def get_user_category_label(user: Any) -> str:
    try:
        from app.services.personnel.categories import get_user_personnel_category_label

        return normalize_category_label(get_user_personnel_category_label(user))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        related = getattr(user, "performance_category", None)
        for attr in ("name", "label", "title"):
            value = getattr(related, attr, None)
            if value:
                return normalize_category_label(value)
        return normalize_category_label(getattr(user, "personnel_category", None))


def user_matches_category(user: Any, category_label: Any) -> bool:
    return get_user_category_label(user) == normalize_category_label(category_label)


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None


def _score_from_item(item: Any) -> float | None:
    keys = ("final_score", "final_total_100", "report_final_score", "average_score", "avg_score", "score", "total_score")
    if isinstance(item, dict):
        for key in keys:
            val = _safe_float(item.get(key))
            if val is not None:
                return val
    for key in keys:
        val = _safe_float(getattr(item, key, None))
        if val is not None:
            return val
    return None


def category_average_without_person_detail(items: Iterable[Any] | None, category_label: Any | None = None) -> dict[str, Any]:
    values: list[float] = []
    wanted = normalize_category_label(category_label) if category_label else None
    for item in items or []:
        user = item.get("user") if isinstance(item, dict) else getattr(item, "user", None)
        if user is None:
            user = item.get("employee") if isinstance(item, dict) else getattr(item, "employee", None)
        current_label = None
        if user is not None:
            current_label = get_user_category_label(user)
        else:
            current_label = normalize_category_label(item.get("personnel_category") if isinstance(item, dict) else getattr(item, "personnel_category", None))
        if wanted and current_label != wanted:
            continue
        score = _score_from_item(item)
        if score is not None:
            values.append(score)
    label = wanted or "Tüm Kategoriler"
    average = round(sum(values) / len(values), 2) if values else 0.0
    return CategoryAverageSummary(label, average, len(values)).as_dict()


def build_category_average_summary_for_users(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Eski/yeni çağrıları destekleyen gizlilik güvenli özet fonksiyonu."""
    try:
        from app.services.performance.category_stats import build_category_average_summary_for_users as legacy_builder

        summary = legacy_builder(*args, **kwargs)
        if isinstance(summary, dict):
            summary["detail_visible"] = False
            summary["person_detail_visible"] = False
            summary["privacy_note"] = summary.get("privacy_note") or PRIVACY_NOTE
            return summary
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        import logging
        logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/phase2_category_center.py")
    items = args[0] if args else kwargs.get("items") or []
    label = kwargs.get("selected_category") or kwargs.get("category_label") or kwargs.get("personnel_category")
    return category_average_without_person_detail(items, label)


def catalog_rows_for_gate() -> list[dict[str, str]]:
    return [
        {
            "module_key": module_key,
            "setting_key": setting_key,
            "full_key": f"{module_key}.{setting_key}",
            "label": label,
            "value_type": value_type,
            "default": default,
            "description": description,
        }
        for module_key, setting_key, label, value_type, default, description in PHASE2_SETTING_ROWS
    ]


__all__ = [
    "PHASE2_CATEGORY_CENTER_VERSION",
    "BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_CENTER",
    "DEFAULT_CATEGORY_ROWS",
    "DEFAULT_CATEGORY_LABELS",
    "PRIVACY_NOTE",
    "PHASE2_SETTING_ROWS",
    "normalize_category_label",
    "slugify_category",
    "get_category_options",
    "ensure_category",
    "seed_default_categories",
    "assign_user_category",
    "get_user_category_label",
    "user_matches_category",
    "category_average_without_person_detail",
    "build_category_average_summary_for_users",
    "catalog_rows_for_gate",
]
