"""İK tarih aralığı kuralları için saf yardımcılar."""
from __future__ import annotations

from datetime import date


def date_ranges_overlap(existing_start: date, existing_end: date, new_start: date, new_end: date) -> bool:
    """Kapalı aralık çakışması.

    Aynı gün biten/başlayan izinler çakışır kabul edilir; çünkü iki kayıt aynı
    takvim gününü paylaşır. Bitiş başlangıçtan önceyse aralık geçersizdir.
    """
    if not all([existing_start, existing_end, new_start, new_end]):
        return False
    if existing_end < existing_start or new_end < new_start:
        return False
    return existing_start <= new_end and existing_end >= new_start
