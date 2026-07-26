# BYS360 — Mypy Borç Envanteri (Campaign 2 Girdisi)

**Üretildiği kampanya:** Truthful Quality Gates (Campaign 1) — koordinatör ek analizi
**Amaç:** Bu envanter yalnız kayıt amaçlıdır. Campaign 1 kapsamında hiçbir hata düzeltilmedi,
ignore/exclude eklenmedi, kapsam daraltılmadı. Aşağıdaki 541 bulgu, mypy CI komutunun artık
yapısal olarak çökmeden tamamlanabilmesi (bkz. `[tool.mypy]` `explicit_package_bases`/`mypy_path`
düzeltmesi) sonucunda ilk kez ölçülebilir hale gelmiştir.

**Komut:** `mypy app tests scripts --ignore-missing-imports --no-error-summary`
**Çalıştıran ortam:** `C:\bys360\project\.venv\Scripts\python.exe` (mypy 2.3.0)
**Toplam bulgu:** 541 (tests/: 203, scripts/: 338)
**Baz alınan HEAD:** `9816259` + Campaign 1'in `[tool.mypy]` config düzeltmesi (uncommitted, çalışma ağacında)

## Alan bazında dağılım

| Alan | Hata sayısı |
|---|---|
| tests/ | 203 |
| scripts/ | 338 |

## tests/ — kural koduna göre dağılım

| Kod | Sayı |
|---|---|
| attr-defined | 72 |
| arg-type | 69 |
| var-annotated | 13 |
| assignment | 11 |
| unused-ignore | 9 |
| index | 8 |
| union-attr | 6 |
| misc | 5 |
| operator | 4 |
| list-item | 3 |
| has-type | 1 |
| used-before-def | 1 |
| override | 1 |

## scripts/ — kural koduna göre dağılım

| Kod | Sayı |
|---|---|
| union-attr | 91 |
| attr-defined | 62 |
| index | 40 |
| arg-type | 36 |
| var-annotated | 27 |
| unused-ignore | 21 |
| assignment | 20 |
| call-overload | 12 |
| dict-item | 10 |
| return-value | 8 |
| operator | 6 |
| type-var | 2 |
| misc | 2 |
| no-redef | 1 |

## İlk 20 dosya (hata sayısına göre)

| # | Hata | Dosya |
|---|---|---|
| 1 | 33 | tests/services/test_settings_campaign2_wave2_phase4du.py |
| 2 | 17 | scripts/archive/quality/phase2y-wave1/analyze_p11_g_evaluation_template_inventory_v1.py |
| 3 | 16 | scripts/archive/pre_handover_20260708/dashboard/emergency_rollback_executive_summary_v1_0_8.py |
| 4 | 16 | tests/services/test_settings_snapshots_phase4bx.py |
| 5 | 15 | scripts/quality/bys360_mobile_performance_response_gate_p3e.py |
| 6 | 14 | scripts/archive/pre_handover_20260708/performance/check_bys360_performance_completion_phase12_final_gate.py |
| 7 | 13 | scripts/archive/quality/phase2y-wave1/bys360_repo_hygiene_p0_2_active_audit_health_v2_17_3.py |
| 8 | 13 | scripts/archive/quality/phase2y-wave1/apply_p14_e_assistant_js_helper_split_apply_v1.py |
| 9 | 13 | scripts/archive/quality/phase2y-wave1/apply_p14_e2_assistant_js_helper_split_safe_apply_v1.py |
| 10 | 13 | tests/services/test_low_score_process_service_phase4t.py |
| 11 | 12 | tests/architecture/conftest.py |
| 12 | 12 | scripts/archive/quality/phase2y-wave1/analyze_p12_a_technical_ui_term_inventory_v1.py |
| 13 | 12 | tests/behavior/test_feedback_campaign_behavior.py |
| 14 | 11 | scripts/quality/bys360_mobile_security_suite_gate_p4c_v2.py |
| 15 | 11 | scripts/quality/bys360_mobile_security_suite_gate_p4c.py |
| 16 | 9 | scripts/archive/quality/phase2y-wave1/analyze_p11_d1_menu_registry_data_candidates_v1.py |
| 17 | 9 | scripts/archive/pre_handover_20260708/live_readiness/a7d_local_smoke_contract.py |
| 18 | 9 | scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3.py |
| 19 | 8 | tests/services/test_settings_campaign2_wave1_phase4dt.py |
| 20 | 8 | scripts/archive/quality/phase2y-wave1/analyze_p14_f_assistant_js_split_verification_v1.py |

## Gözlem (kayıt amaçlı, karar değil)

`scripts/` hatalarının büyük bölümü `scripts/archive/**` altındaki, artık aktif kullanılmayan
(arşivlenmiş) betiklerde toplanıyor. Bu envanterin ürettiği tek karar önerisi şudur: sonraki
teknik borç kampanyası, `scripts/archive/**`'in mypy kapsamına dahil edilip edilmeyeceğine
(bilinçli bir config kararı olarak, Campaign 1'in yasakladığı "sessiz exclude" değil) açıkça
karar vermelidir. Bu envanter kararı vermez, yalnız veriyi kaydeder.

## Durum

`REVIEW` — Gate yapısal olarak çalışıyor (artık çökmüyor) ve gerçek sonucu (541 bulgu) gösteriyor.
Bu 541 bulgu, sonraki teknik borç kampanyasına (SAFE/CONTROLLED/REVIEW/BLOCKED sınıflandırması ve
paket bazlı düzeltme disiplinine tabi olarak) devredilir.
