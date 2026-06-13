# -*- coding: utf-8 -*-
from __future__ import annotations



import logging
"""BYS360 Faz 4.4 - 3. amir ekran sütunu görünürlük yardımcısı.

Kural: 3. amir verisi yoksa tablo/listelerde boş sütun gösterilmez. Form tarafında
ayar izin veriyorsa alan gösterilebilir; böylece yetkili kullanıcı gerektiğinde 3. amir
ataması yapabilir.
"""

from typing import Any, Iterable
logger = logging.getLogger(__name__)

# BYS360_PHASE4_4_THIRD_SUPERVISOR_SCREEN_COLUMN

THIRD_SUPERVISOR_KEYS = {
    "level_3", "level_3_id", "level_3_name", "level_3_sicil", "level_3_manager_id",
    "level_3_manager_sicil", "level_3_total_100", "third_supervisor", "third_supervisor_id",
    "third_supervisor_name", "third_supervisor_sicil", "third_manager", "third_manager_id",
    "third_manager_name", "third_manager_sicil", "manager_3_id", "manager_3_name",
    "manager_3_sicil", "ucuncu_yonetici_sicil", "üçüncü_yönetici_sicil",
}

EMPTY_VALUES = {None, "", "-", "—", "None", "none", "NULL", "null", 0, "0"}


def _is_present(value: Any) -> bool:
    if value in EMPTY_VALUES:
        return False
    if isinstance(value, str) and value.strip() in EMPTY_VALUES:
        return False
    return True


def _iter_values(obj: Any) -> Iterable[Any]:
    if obj is None:
        return []
    if isinstance(obj, dict):
        return obj.values()
    if isinstance(obj, (list, tuple, set)):
        return obj
    rows = getattr(obj, "rows", None)
    if rows is not None and rows is not obj:
        return rows
    return [obj]


def _get_value(obj: Any, key: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def has_third_supervisor_data(rows: Any = None, *, selected_value: Any = None) -> bool:
    """Veri setinde gerçek 3. amir/3. amir puanı var mı?"""
    if _is_present(selected_value):
        return True
    for item in _iter_values(rows):
        if item is None:
            continue
        # Bazı karne satırlarında evaluation nesnesi iç içe gelir.
        nested = [_get_value(item, "evaluation"), _get_value(item, "assignment"), _get_value(item, "chain")]
        for key in THIRD_SUPERVISOR_KEYS:
            if _is_present(_get_value(item, key)):
                return True
        for child in nested:
            if child is not None:
                for key in THIRD_SUPERVISOR_KEYS:
                    if _is_present(_get_value(child, key)):
                        return True
        # Görev satırı seviyesi 3 ise 3. amir gerçek veri kabul edilir.
        try:
            if int(_get_value(item, "manager_level") or 0) == 3:
                return True
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/third_supervisor_column_visibility.py")
    return False


def _policy_allows_column(period: Any | None = None) -> bool:
    try:
        from app.services.performance.third_supervisor_policy import third_supervisor_policy_snapshot
        snapshot = third_supervisor_policy_snapshot(period)
        return bool(snapshot.get("enabled") and snapshot.get("show_column"))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


def should_show_third_supervisor_column(rows: Any = None, period: Any | None = None, *, selected_value: Any = None, allow_setting: bool = False) -> bool:
    """Tablo/form 3. amir sütunu/alanı gösterilsin mi?

    Liste ve raporlarda allow_setting=False kullanılmalıdır: veri yoksa boş sütun çıkmaz.
    Formlarda allow_setting=True kullanılabilir: ayar açıksa 3. amir alanı ekleme için görünür.
    """
    if has_third_supervisor_data(rows, selected_value=selected_value):
        return True
    if allow_setting and _policy_allows_column(period):
        return True
    return False


__all__ = [
    "has_third_supervisor_data",
    "should_show_third_supervisor_column",
]
