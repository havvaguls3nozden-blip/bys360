# BYS360 — Ruff "Full-Select" Gate Borç Envanteri (Campaign 2 Girdisi)

**Üretildiği kampanya:** Truthful Quality Gates (Campaign 1) — koordinatör ek analizi
**Amaç:** Bu envanter yalnız kayıt amaçlıdır. Gate kapsamı daraltılmadı, hiçbir kural config
üzerinden kapatılmadı, hiçbir satıra `# noqa` eklenmedi. Mevcut kırmızı durum olduğu gibi
raporlanmıştır.

**Komut (CI'nin "Ruff F821 hard gate" adımıyla birebir aynı):**
`ruff check app config.py wsgi.py run.py scripts tests`
**Çalıştıran ortam:** `C:\bys360\project\.venv\Scripts\python.exe` (ruff 0.15.21)
**Toplam bulgu (bu ölçümde):** 41
**Not — sayı hareketli:** Campaign 1'in aynı anda çalışan başka bir ajanı `tests/conftest.py`
dosyasını (ci_safe marker mekanizması için, ayrı bir teslimatta) değiştirdiği için bu sayı,
kampanya başlangıcındaki referans değer olan 42'den 41'e düşmüştür (E402: 18→16, yeni: F811×1).
Bu, ruff gate'inin kasıtlı olarak düzeltildiği anlamına GELMEZ — conftest.py değişikliğinin yan
etkisidir ve final entegrasyon raporunda ayrıca doğrulanacaktır.

## Kural koduna göre dağılım

| Kod | Sayı |
|---|---|
| E402 | 16 |
| UP022 | 5 |
| B010 | 5 |
| I001 | 4 |
| B018 | 3 |
| B034 | 2 |
| E401 | 1 |
| F811 | 1 |
| SIM117 | 1 |
| UP037 | 1 |
| SIM300 | 1 |
| UP012 | 1 |

## Dosyaya göre dağılım

| Sayı | Dosya |
|---|---|
| 8 | tests/services/test_ai_excel_preview_phase4w.py |
| 5 | tests/conftest.py |
| 4 | tests/services/test_mobile_service_delegates_phase4z.py |
| 3 | scripts/local/file_center_ops_tick_v1l.py |
| 3 | tests/services/test_mobile_personnel_service_phase4aj.py |
| 2 | scripts/communication/run_corporate_information_task.py |
| 2 | scripts/communication/run_executive_mail_center_v2.py |
| 2 | scripts/quality/bys360_pytest_standard_gate_p2d.py |
| 2 | scripts/release/build_bys360_safe_release.py |
| 3 | tests/architecture/conftest.py |
| 1 | scripts/communication/send_daily_evening_tomorrow_mail.py |
| 1 | scripts/communication/send_daily_pulse_check_mail.py |
| 1 | scripts/quality/bys360_mobile_pytest_contract_gate_p2a_v3.py |
| 1 | tests/architecture/test_android_responsive_completion_v1.py |
| 1 | tests/architecture/test_android_responsive_completion_v2.py |
| 1 | tests/performance/test_president_low_score_card_sql_identifier_phase5r.py |
| 1 | tests/services/test_mobile_assistant_service_phase4al.py |
| 1 | tests/services/test_mobile_performance_period_service_phase4ad.py |
| 1 | tests/services/test_mobile_performance_task_service_phase4ab.py |
| 1 | tests/services/test_mobile_survey_service_phase4ah.py |

## Dosya × kural detayı

```
E402     scripts/communication/run_corporate_information_task.py:12
E402     scripts/communication/run_corporate_information_task.py:13
I001     scripts/communication/run_executive_mail_center_v2.py:1
E401     scripts/communication/run_executive_mail_center_v2.py:2
I001     scripts/communication/send_daily_evening_tomorrow_mail.py:1
I001     scripts/communication/send_daily_pulse_check_mail.py:1
E402     scripts/local/file_center_ops_tick_v1l.py:11
E402     scripts/local/file_center_ops_tick_v1l.py:12
E402     scripts/local/file_center_ops_tick_v1l.py:13
UP022    scripts/quality/bys360_mobile_pytest_contract_gate_p2a_v3.py:99
B034     scripts/quality/bys360_pytest_standard_gate_p2d.py:46
B034     scripts/quality/bys360_pytest_standard_gate_p2d.py:47
UP022    scripts/release/build_bys360_safe_release.py:54
UP022    scripts/release/build_bys360_safe_release.py:62
B018     tests/architecture/conftest.py:37
B018     tests/architecture/conftest.py:51
B018     tests/architecture/conftest.py:65
UP022    tests/architecture/test_android_responsive_completion_v1.py:19
UP022    tests/architecture/test_android_responsive_completion_v2.py:19
F811     tests/conftest.py:56
SIM117   tests/conftest.py:89
UP037    tests/performance/test_president_low_score_card_sql_identifier_phase5r.py:36
E402     tests/services/test_ai_excel_preview_phase4w.py:9
E402     tests/services/test_ai_excel_preview_phase4w.py:10
E402     tests/services/test_ai_excel_preview_phase4w.py:11
E402     tests/services/test_ai_excel_preview_phase4w.py:13
E402     tests/services/test_ai_excel_preview_phase4w.py:14
E402     tests/services/test_ai_excel_preview_phase4w.py:16
SIM300   tests/services/test_ai_excel_preview_phase4w.py:22
UP012    tests/services/test_ai_excel_preview_phase4w.py:183
B010     tests/services/test_mobile_assistant_service_phase4al.py:36
E402     tests/services/test_mobile_performance_period_service_phase4ad.py:14
E402     tests/services/test_mobile_performance_task_service_phase4ab.py:14
B010     tests/services/test_mobile_personnel_service_phase4aj.py:55
B010     tests/services/test_mobile_personnel_service_phase4aj.py:69
B010     tests/services/test_mobile_personnel_service_phase4aj.py:83
E402     tests/services/test_mobile_service_delegates_phase4z.py:10
I001     tests/services/test_mobile_service_delegates_phase4z.py:10
E402     tests/services/test_mobile_service_delegates_phase4z.py:11
E402     tests/services/test_mobile_service_delegates_phase4z.py:12
B010     tests/services/test_mobile_survey_service_phase4ah.py:34
```

## Zaten devam eden ilgili çalışma

Bu 41 bulgunun tamamını sıfıra indirme görevi bu kampanyanın kapsamında değildir. Repoda halihazırda
bu amaca yönelik ayrı bir worktree/branch bulunuyor: `phase5-ruff-tests-cleanup-v1`
(`C:\bys360\worktrees\phase5-ruff-tests-cleanup`). Sonraki teknik borç kampanyası bu branch'in
durumuyla mutabakat sağlamalıdır.

## Durum

`REVIEW` — Gate yapısal olarak çalışıyor ve gerçek sonucu (41 bulgu, kırmızı) dürüstçe gösteriyor.
Kapsam daraltılmadı, suppression eklenmedi. Sıfıra indirme işi sonraki teknik borç kampanyasına
devredilir.
