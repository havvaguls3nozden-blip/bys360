"""BYS360 live preflight merge SP-1A and v58 branches

Revision ID: 20260513_perf_live_gate_merge
Revises: v58a1c2d3e4f, 20260508_sp1a
Create Date: 2026-05-13
"""

from __future__ import annotations

# Bu migration veri/şema değiştirmez; iki bağımsız Alembic başlığını tek canlı başlıkta birleştirir.
# Mevcut durum:
# - v58a1c2d3e4f ana canlı zincirde
# - 20260508_sp1a SP-1A stratejik performans/KPI dalında bağımsız head olarak duruyor
# Bu merge dosyası eklendiğinde `flask db heads` tek head göstermelidir.

revision = "20260513_perf_live_gate_merge"
down_revision = ("v58a1c2d3e4f", "20260508_sp1a")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alembic merge marker. Şema değişikliği bilerek yapılmaz.
    pass


def downgrade() -> None:
    # Canlı geri dönüşte veri kaybı oluşmaması için işlem yapılmaz.
    pass
