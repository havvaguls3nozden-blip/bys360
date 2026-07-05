"""Dijital Arşiv servis iskeleti."""


class DigitalArchiveFeatureDisabled(RuntimeError):
    """Dijital Arşiv modülü kapalıyken işlem istenirse kullanılır."""


def get_module_status():
    """DA-1A modül durum bilgisini döndürür."""
    return {
        "module": "digital_archive",
        "enabled": False,
        "phase": "DA-1A",
        "message": "Dijital Arşiv modülü local geliştirme aşamasındadır.",
    }
