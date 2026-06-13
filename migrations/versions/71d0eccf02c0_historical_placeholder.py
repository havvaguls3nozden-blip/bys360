"""Historical placeholder revision for missing BYS360 migration chain link.

Revision ID: 71d0eccf02c0
Revises:
Create Date: 2026-05-23 08:37:32

Bu dosya, temiz devir paketi migration zincirinde eski down_revision referansı eksik olduğu için oluşturulmuştur.
Özgün revision dosyası mevcut eski proje klasöründe de bulunamamıştır.
Bu placeholder, Alembic revision grafiğini bozmadan mevcut canlı/geri yüklenmiş veritabanı üzerinde migration komutlarının çalışabilmesi için eklenmiştir.
Yeni sıfır veritabanı kurulumu yapılacaksa, ayrıca güncel şema baseline/migration doğrulaması yapılmalıdır.
"""
from alembic import op
import sqlalchemy as sa


revision = '71d0eccf02c0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
