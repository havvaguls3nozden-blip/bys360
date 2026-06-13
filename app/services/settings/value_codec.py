"""BYS360 ayar deger donusum yardimcilari.

Settings Service Tamamlama Faz 1:
- settings_service.py icindeki okuma/yazma deger kodlama fonksiyonlarini ayirir.
- Veritabani semasina dokunmaz.
- Dis API sozlesmesini korur; settings_service.py ayni fonksiyon adlarini kullanmaya devam eder.
"""
from __future__ import annotations


from typing import Any


def normalize_bool(value: Any) -> bool:
    """Form/veritabani metin degerini guvenli bool karsiligina cevirir."""
    normalized = str(value or "").strip().lower()
    return normalized in {"1", "true", "on", "yes", "evet", "aktif"}


def value_to_storage(value: Any, value_type: str) -> str:
    """Ayar degerini veritabaninda saklanacak metin temsiline cevirir."""
    if value_type == "bool":
        return "true" if normalize_bool(value) else "false"
    if value_type == "int":
        try:
            return str(int(str(value or "0").strip() or 0))
        except (TypeError, ValueError):
            return "0"
    return str(value or "").strip()


def value_to_python(value_text: str | None, value_type: str) -> Any:
    """Ayar degerini arayuzde kullanilacak Python degerine cevirir."""
    raw = (value_text or "").strip()
    if value_type == "bool":
        return normalize_bool(raw)
    if value_type == "int":
        try:
            return int(raw or 0)
        except (TypeError, ValueError):
            return 0
    return raw


__all__ = [
    "normalize_bool",
    "value_to_python",
    "value_to_storage",
]
