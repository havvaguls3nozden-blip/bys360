# BYS360 Aşama 5 Test Triage Aksiyon Planı

Bu rapor testleri otomatik silmez veya değiştirmez. Ama başarısız/hatalı testleri güvenli aksiyon sınıflarına ayırır.

## Genel Durum

- Toplam test case: **1063**
- error: **45**
- failed: **246**
- passed: **770**
- skipped: **2**
- Failed + Error: **291**

## Aksiyon Sayıları

- archive_or_delete_obsolete_contract: **218**
- fix_test_infra: **38**
- fix_runtime_or_route_contract: **14**
- fix_runtime_or_contract: **7**
- archive_or_split_mobile_evidence: **7**
- move_to_live_realdb_slow_marker: **4**
- manual_review: **2**
- fix_or_mark_realdb_contract: **1**

## Öncelik Sırası

### P0 — Test altyapısını düzelt
`fixture 'app' not found` hataları çok sayıda testi tek kökten bozuyor. Önce `tests/critical/conftest.py` veya kök `tests/conftest.py` altında `app` ve `client` fixture sözleşmesi netleştirilmeli.

### P1 — Eski faz/evidence sözleşmelerini arşivle veya sil
Sprint2/Sprint3/Faz/Release evidence testlerinin çoğu bugünkü runtime kalitesini değil geçmiş dosya varlığını test ediyor. Geçersiz olanlar `tests/archive/` altına alınmalı veya silinmeli.

### P1 — live/realdb/slow marker ayrımı
Canlı, dış servis, deployment, PostgreSQL veya gerçek DB isteyen testler varsayılan CI’dan çıkarılıp açık marker ile çalıştırılmalı.

### P2 — Gerçek runtime/modül sözleşmelerini düzelt
Auth, feedback, performance, portal, communication ve AI repository testlerinden gerçekten canlı davranışı ölçenler korunmalı ve düzeltilmeli.

## Üretilen Dosyalar

- decisions_csv: `C:\bys360\project\reports\quality\BYS360_A5_TEST_TRIAGE_DECISIONS.csv`
- action_plan_md: `C:\bys360\project\reports\quality\BYS360_A5_TEST_TRIAGE_ACTION_PLAN.md`
- summary_json: `C:\bys360\project\reports\quality\BYS360_A5_TEST_TRIAGE_SUMMARY.json`
- archive_or_delete_candidates: `C:\bys360\project\reports\quality\BYS360_A5_ARCHIVE_OR_DELETE_CANDIDATES.txt`
- fix_first_candidates: `C:\bys360\project\reports\quality\BYS360_A5_FIX_FIRST_CANDIDATES.txt`
- marker_move_candidates: `C:\bys360\project\reports\quality\BYS360_A5_MARKER_MOVE_CANDIDATES.txt`
