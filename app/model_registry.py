
"""BYS360 kanonik model export yüzeyi.

Canlı öncesi temizlik Faz 3:
- model export listesi tek tek sabit import yerine ``app.models`` üzerinden okunur
- kaldırılan modüller stub/export uyumluluğu ile yönetilir
- registry yüzeyi ``app.models.__all__`` ile senkron kalır
"""
from __future__ import annotations

from app import models as _models

MODEL_EXPORTS = tuple(name for name in getattr(_models, "__all__", ()) if isinstance(name, str))

for _name in MODEL_EXPORTS:
    globals()[_name] = getattr(_models, _name)

def exported_model_names():
    """Dışa açılan model isimlerini alfabetik olarak döndürür."""
    return sorted(set(MODEL_EXPORTS))

__all__ = [*MODEL_EXPORTS, "MODEL_EXPORTS", "exported_model_names"]
