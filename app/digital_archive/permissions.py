"""Dijital Arşiv izin ve modül durumu yardımcıları."""

MODULE_SETTING_KEY = "digital_archive_enabled"

_ENABLED_VALUES = {"1", "true", "yes", "on", "enabled", "aktif", "acik", "açık"}


def normalize_setting_value(value):
    """Ayar değerini güvenli karşılaştırma için metne çevirir."""
    if value is None:
        return ""
    return str(value).strip().lower()


def is_digital_archive_enabled(value=None):
    """Dijital Arşiv modülünün açık olup olmadığını döndürür.

    Varsayılan kapalıdır. Böylece modül yanlışlıkla canlı davranış üretmez.
    """
    return normalize_setting_value(value) in _ENABLED_VALUES
