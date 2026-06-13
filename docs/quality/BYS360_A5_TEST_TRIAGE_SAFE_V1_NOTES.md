# BYS360 A5 Test Triage SAFE V1

Bu paket testleri silmez, değiştirmez ve CI dosyalarını otomatik güncellemez.
Ama `BYS360_A5_FULL_TESTS_JUNIT.xml` veya `BYS360_A5_TEST_FAILURE_TRIAGE.csv` üzerinden başarısız/hatalı testleri aksiyon sınıflarına ayırır.

Üretilen raporlar:

- `reports/quality/BYS360_A5_TEST_TRIAGE_DECISIONS.csv`
- `reports/quality/BYS360_A5_TEST_TRIAGE_ACTION_PLAN.md`
- `reports/quality/BYS360_A5_TEST_TRIAGE_SUMMARY.json`
- `reports/quality/BYS360_A5_ARCHIVE_OR_DELETE_CANDIDATES.txt`
- `reports/quality/BYS360_A5_FIX_FIRST_CANDIDATES.txt`
- `reports/quality/BYS360_A5_MARKER_MOVE_CANDIDATES.txt`

Aksiyon türleri:

- `fix_test_infra`: pytest fixture/test altyapısı önce düzeltilmeli.
- `archive_or_delete_obsolete_contract`: eski Faz/Sprint/evidence sözleşmeleri arşivlenmeli veya silinmeli.
- `move_to_live_realdb_slow_marker`: canlı/realdb/dış servis testleri varsayılan CI dışına alınmalı.
- `fix_runtime_or_contract`: hâlâ değerli iş kuralı/modül sözleşmeleri düzeltilmeli.
- `manual_review`: elle karar gerekenler.
