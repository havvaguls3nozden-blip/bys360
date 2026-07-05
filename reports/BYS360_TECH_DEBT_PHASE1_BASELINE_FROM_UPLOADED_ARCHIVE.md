# BYS360 Teknik Borç Faz 1 — Yüklenen Arşiv Ön Audit Raporu

Kaynak arşiv: `bys360 (26).zip`  
Bu rapor, bu konuşmaya yüklenen arşiv üzerinden üretildi. Yerelde çalıştırılacak overlay raporu ayrıca kendi bilgisayarındaki güncel klasöre göre tekrar üretir.

## Yönetici Özeti

| Ölçüm | Değer |
|---|---:|
| Toplam dosya | 14334 |
| Sıkıştırılmış boyut | 429.97 MB |
| Açılmış boyut | 716.80 MB |
| Temiz kaynak adayı | 3603 |
| Ayrılması gereken/generated dosya | 10731 |

## İlk Tespit

Paketin büyük kısmı kaynak kod değil; sanal ortam, git geçmişi, loglar, yerel veri tabanı, nested release zipleri ve build/cache dosyalarından oluşuyor. Bu yüzden ilk fazın amacı kodu kırmadan proje klasörünü temiz kaynak/yedek/log/release ayrımına geçirmek olmalıdır.

## Riskli Dosya Aileleri

| Risk | Adet | Örnek |
|---|---:|---|
| .env included | 1 | `bys360/project/.env` |
| git history included | 91 | `bys360/project/.git/COMMIT_EDITMSG, bys360/project/.git/config, bys360/project/.git/description` |
| venv included | 9017 | `bys360/project/.venv/Include/site/python3.12/greenlet/greenlet.h, bys360/project/.venv/Lib/site-packages/81d243bd2c585b0f4821__mypyc.cp312-win_amd64.pyd, bys360/project/.venv/Lib/site-packages/alembic/autogenerate/api.py` |
| sqlite included | 1 | `bys360/project/instance/bys360_local_dev.sqlite3` |
| log included | 75 | `bys360/project/.git/logs/HEAD, bys360/project/.git/logs/refs/heads/code-quality-architecture-score-v1, bys360/project/.git/logs/refs/heads/handover-docs-v1` |
| nested release zip included | 3 | `bys360/project/dist_secure/BYS360_SECURE_RELEASE_V1_5_20260624_121314.zip, bys360/project/dist_secure/BYS360_SECURE_RELEASE_V1_5_20260624_124957.zip, bys360/project/dist_secure/BYS360_SECURE_RELEASE_V1_5_20260625_131641.zip` |
| flutter build cache included | 77 | `bys360/project/.venv/Lib/site-packages/pip/_internal/operations/build/build_tracker.py, bys360/project/.venv/Lib/site-packages/pip/_internal/operations/build/metadata.py, bys360/project/.venv/Lib/site-packages/pip/_internal/operations/build/metadata_editable.py` |
| cache files included | 1959 | `bys360/project/.ruff_cache/.gitignore, bys360/project/.ruff_cache/0.15.17/10561034126196602729, bys360/project/.ruff_cache/0.15.17/10616114117444164289` |

## Kod Göstergeleri

| Ölçüm | Değer |
|---|---:|
| `app` Python dosyası | 1004 |
| `app` Python satırı | 240289 |
| Route tanımı | 877 |
| Fonksiyon tanımı | 8776 |
| Class tanımı | 619 |

## Desen Sayımları

| Desen | Adet |
|---|---:|
| TODO/FIXME/HACK | 14 |
| broad except | 2798 |
| hardcoded localhost | 91 |
| print calls | 2786 |
| raw traceback/debug | 10 |
| secret-like text | 989 |
| technical UI words | 36596 |

> Not: Desen sayımları otomatik taramadır. Örneğin “technical UI words” kod içinde, dokümanda veya testlerde geçebilir; her biri kullanıcı ekranında hata var anlamına gelmez. Faz 2'de bu sayımlar modül bazında ayrıştırılmalıdır.

## En Büyük Dosyalar

- 100.82 MB — `bys360/project/dist_secure/BYS360_SECURE_RELEASE_V1_5_20260624_121314.zip`
- 100.32 MB — `bys360/project/dist_secure/BYS360_SECURE_RELEASE_V1_5_20260625_131641.zip`
- 98.72 MB — `bys360/project/dist_secure/BYS360_SECURE_RELEASE_V1_5_20260624_124957.zip`
- 64.45 MB — `bys360/project/mobile_flutter/bys360_mobile_native/.dart_tool/flutter_build/ad1d25ab6fe075713787bce9051bba83/app.dill`
- 19.46 MB — `bys360/project/.venv/Lib/site-packages/numpy.libs/libscipy_openblas64_-b788215d9d47792bcba3a2e2a7114320.dll`
- 18.89 MB — `bys360/project/reports/architecture/BYS360_PHASE4C_PERFORMANCE_CATEGORY_SCOPE_INVENTORY_V1_REPORT.json`
- 16.64 MB — `bys360/project/.git/objects/pack/pack-425258d94e022e4bf714e89fbbf5475bf869f9b2.pack`
- 11.03 MB — `bys360/project/mobile_flutter/bys360_mobile_native/.dart_tool/hooks_runner/objective_c/e0ca52924f/hook.dill`
- 11.03 MB — `bys360/project/mobile_flutter/bys360_mobile_native/.dart_tool/hooks_runner/objective_c/b71ed645e9/hook.dill`
- 11.03 MB — `bys360/project/mobile_flutter/bys360_mobile_native/.dart_tool/hooks_runner/objective_c/8e04c28b44/hook.dill`
- 11.03 MB — `bys360/project/mobile_flutter/bys360_mobile_native/.dart_tool/hooks_runner/objective_c/1186d472c4/hook.dill`
- 9.45 MB — `bys360/project/.venv/Lib/site-packages/cryptography/hazmat/bindings/_rust.pyd`
- 9.23 MB — `bys360/project/mobile_flutter/bys360_mobile_native/android/.gradle/8.14/executionHistory/executionHistory.bin`
- 7.53 MB — `bys360/project/.venv/Lib/site-packages/PIL/_avif.cp312-win_amd64.pyd`
- 6.05 MB — `bys360/project/instance/bys360_local_dev.sqlite3`
- 4.95 MB — `bys360/project/reports/quality/BYS360_A5_FULL_TESTS_OUTPUT.txt`
- 3.71 MB — `bys360/project/.venv/Lib/site-packages/numpy/_core/_multiarray_umath.cp312-win_amd64.pyd`
- 2.47 MB — `bys360/project/.venv/Lib/site-packages/PIL/_imaging.cp312-win_amd64.pyd`
- 2.31 MB — `bys360/project/.venv/Lib/site-packages/psycopg2/_psycopg.cp312-win_amd64.pyd`
- 2.13 MB — `bys360/project/.venv/Lib/site-packages/pandas/_libs/groupby.cp312-win_amd64.pyd`

## En Büyük `app/*.py` Dosyaları

- 1568 satır — `bys360/project/app/menu_registry.py`
- 1530 satır — `bys360/project/app/services/performance/low_score_process_service.py`
- 1337 satır — `bys360/project/app/services/ai_agent/service.py`
- 1332 satır — `bys360/project/app/services/settings/catalog.py`
- 1269 satır — `bys360/project/app/file_center/services.py`
- 1244 satır — `bys360/project/app/institutional/hr_personnel_operations_routes.py`
- 1235 satır — `bys360/project/app/main_handlers/account_communication_helpers.py`
- 1203 satır — `bys360/project/app/admin/ai_routes.py`
- 1169 satır — `bys360/project/app/support/routes.py`
- 1165 satır — `bys360/project/app/api/mobile/performance_routes.py`
- 1156 satır — `bys360/project/backups/file_center_local_v1k_20260703_224612/app/file_center/services.py`
- 1150 satır — `bys360/project/app/admin/routes.py`
- 1136 satır — `bys360/project/app/performance/engagement_feedback_routes.py`
- 1127 satır — `bys360/project/app/file_center/routes.py`
- 1073 satır — `bys360/project/app/communication/surveys_routes.py`
- 1066 satır — `bys360/project/app/workflow/routes.py`
- 1059 satır — `bys360/project/app/support/help_center_content.py`
- 1051 satır — `bys360/project/backups/file_center_local_v1kd_role_matrix_20260703_231233/app/file_center/routes.py`
- 1040 satır — `bys360/project/app/services/ai/dashboard_panel_personnel.py`
- 1016 satır — `bys360/project/app/services/performance/process_engine_phase6_president_approvals.py`

## Faz 1 Kararı

1. `.env`, `.git`, `.venv`, `instance/*.sqlite3`, `logs`, `dist_secure`, `archive`, `backups`, `.dart_tool`, `.gradle`, `__pycache__` temiz kaynak paketine alınmayacak.
2. Mevcut klasör silinmeyecek; temiz kaynak ayrı üretilecek.
3. Kod refactor ve büyük dosya bölme Faz 2'de yapılacak.
4. Canlı sistem için ayrı yedek + release + rollback kuralı korunacak.
