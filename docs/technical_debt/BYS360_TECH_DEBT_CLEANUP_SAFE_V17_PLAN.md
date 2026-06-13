# SAFE V17 Plan

Amaç: teknik borç temizliğinde kod dışı güvenlik hijyeni.

Kapsam:
- `.env` varlığını doğrula, anahtar listesini değer göstermeden raporla.
- `.env.example` varlığını doğrula.
- `instance` altındaki yerel SQLite dosyalarını raporla.
- Dosyaların SHA256 hash ve boyut bilgisini üret.
- Hassas/yerel dosyaları proje dışı yedek alanına kopyala.
- `.gitignore` koruma bloğunu ekle/güncelle.

Kapsam dışı:
- `.env` silme.
- SQLite silme.
- Python/HTML/JS iş mantığı değişikliği.
- Gizli değerleri rapora yazma.
