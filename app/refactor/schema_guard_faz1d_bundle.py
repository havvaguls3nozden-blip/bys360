"""
Faz 1D için schema_guard review bundle.
Bu dosya doğrudan import edilmek zorunda değildir; apply script bunu okuyup
review edilebilir aday dosya üretir.
"""

BUNDLE_TEXT = r"""
# ---- Faz 1D schema guard review bundle ----
# Aşağıdaki bloklar mevcut schema_guard.py dosyasına doğrudan kör şekilde
# yazılmak yerine önce candidate olarak üretilir ve gözden geçirilir.

# ---- Faz 7 snippet özeti ----
from app.schema_guard_phase7_snippet import PHASE7_TABLE_REPAIRS, PHASE7_COLUMN_REPAIRS

# ---- Faz 8 snippet özeti ----
from app.schema_guard_phase8_snippet import PHASE8_TABLE_REPAIRS, PHASE8_COLUMN_REPAIRS

# ---- Faz 8.1 snippet özeti ----
# app/schema_guard_faz81_snippet.py içindeki stabilizasyon blokları review için aday dosyaya eklenir.
"""