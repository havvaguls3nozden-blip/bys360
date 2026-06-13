# BYS360 P1A Mimari Route Envanteri

Üretim zamanı: `2026-06-09T22:06:30`

## Özet

| Alan | Değer |
|---|---:|
| Taranan Python dosyası | 1782 |
| Route sayısı | 840 |
| Blueprint bulunan dosya | 18 |
| Büyük dosya uyarısı | 120 |
| Kritik/god file | 3 |

## Büyük Dosya Listesi

| Dosya | Satır | Route | Seviye |
|---|---:|---:|---|
| `app/services/corporate_information_center.py` | 2764 | 0 | `critical_god_file` |
| `app/api/mobile/routes.py` | 2379 | 0 | `critical_god_file` |
| `app/services/settings/effective_menu.py` | 2111 | 0 | `critical_god_file` |
| `app/api/mobile/performance_routes.py` | 1789 | 0 | `high_large_file` |
| `app/services/performance/low_score_process_service.py` | 1533 | 0 | `high_large_file` |
| `app/menu_registry.py` | 1515 | 0 | `high_large_file` |
| `app/main_handlers/account_communication_helpers.py` | 1384 | 0 | `high_large_file` |
| `app/services/settings/catalog.py` | 1331 | 0 | `high_large_file` |
| `app/services/ai_agent/service.py` | 1293 | 0 | `high_large_file` |
| `app/institutional/hr_personnel_operations_routes.py` | 1242 | 20 | `high_large_file` |
| `app/admin/ai_routes.py` | 1216 | 17 | `high_large_file` |
| `app/support/routes.py` | 1213 | 23 | `high_large_file` |
| `app/admin/ops_routes.py` | 1207 | 15 | `high_large_file` |
| `app/admin/routes.py` | 1154 | 9 | `high_large_file` |
| `app/performance/engagement_feedback_routes.py` | 1140 | 23 | `high_large_file` |
| `app/communication/surveys_routes.py` | 1074 | 16 | `high_large_file` |
| `app/workflow/routes.py` | 1071 | 12 | `high_large_file` |
| `app/support/help_center_content.py` | 1061 | 0 | `high_large_file` |
| `app/services/performance/process_engine_phase6_president_approvals.py` | 1015 | 0 | `high_large_file` |
| `app/models/hr_models.py` | 1004 | 0 | `high_large_file` |
| `app/services/ai/dashboard_panel_personnel.py` | 1004 | 0 | `high_large_file` |
| `app/services/ai/dashboard_panel_repository.py` | 930 | 0 | `medium_large_file` |
| `app/services/feedback_service.py` | 920 | 0 | `medium_large_file` |
| `app/services/dashboard_rebuild_service.py` | 893 | 0 | `medium_large_file` |
| `app/services/ai_agent/assistant_full_stepwise_tutor_v5.py` | 889 | 0 | `medium_large_file` |
| `app/services/hr_operations_service.py` | 881 | 0 | `medium_large_file` |
| `app/services/communication_phase2_service.py` | 877 | 0 | `medium_large_file` |
| `app/services/ai_agent/assistant_chatgpt_like_v31.py` | 874 | 0 | `medium_large_file` |
| `app/performance/phase10_development_guidance_ui.py` | 867 | 0 | `medium_large_file` |
| `app/portal/routes.py` | 862 | 0 | `medium_large_file` |

## Mobil API Odak Alanı

| Dosya | Satır | Route | Seviye |
|---|---:|---:|---|
| `app/api/mobile/routes.py` | 2379 | 0 | `critical_god_file` |
| `app/api/mobile/performance_routes.py` | 1789 | 0 | `high_large_file` |
| `app/api/mobile/services/auth_service.py` | 121 | 0 | `normal` |
| `app/api/mobile/services/communication_service.py` | 76 | 0 | `normal` |
| `app/api/mobile/services/dashboard_service.py` | 60 | 0 | `normal` |
| `app/api/mobile/services/performance_summary_service.py` | 57 | 0 | `normal` |
| `app/api/mobile/services/performance_period_service.py` | 47 | 0 | `normal` |
| `app/api/mobile/__init__.py` | 34 | 0 | `normal` |
| `app/api/mobile/services/performance_task_service.py` | 32 | 0 | `normal` |
| `app/api/mobile/services/split_manifest.py` | 30 | 0 | `normal` |
| `app/api/mobile/services/survey_service.py` | 30 | 0 | `normal` |
| `app/api/mobile/services/base.py` | 26 | 0 | `normal` |
| `app/api/mobile/services/profile_service.py` | 26 | 0 | `normal` |
| `app/api/mobile/services/__init__.py` | 22 | 0 | `normal` |
| `app/api/mobile/services/personnel_service.py` | 21 | 0 | `normal` |
| `app/api/mobile/communication_read_routes.py` | 20 | 0 | `normal` |
| `app/api/mobile/communication_v2_read_routes.py` | 20 | 0 | `normal` |
| `app/api/mobile/detail_read_routes.py` | 20 | 0 | `normal` |
| `app/api/mobile/light_read_routes.py` | 20 | 0 | `normal` |
| `app/api/mobile/support_survey_read_routes.py` | 20 | 0 | `normal` |
| `app/api/mobile/utility_routes.py` | 20 | 0 | `normal` |
| `app/api/mobile/performance_read_routes.py` | 19 | 0 | `normal` |
| `app/api/mobile/services/support_service.py` | 13 | 0 | `normal` |
| `app/api/mobile/services/assistant_service.py` | 11 | 0 | `normal` |
| `app/api/mobile/services/performance_evaluation_service.py` | 4 | 0 | `normal` |
| `app/api/mobile/services/performance_scorecard_service.py` | 4 | 0 | `normal` |

## P1B için karar notu

Bu rapor kod değiştirmez. Amaç, P1B'de route parçalama ve konsolidasyon yapılırken endpoint kaybı yaşanmaması için mevcut tabloyu sabitlemektir.

Öncelik sırası:
1. `app/api/mobile/routes.py` ve benzeri kritik uzun dosyaları domain bazlı ayırmak.
2. Endpoint isimlerini ve URL sözleşmesini bozmadan geriye uyumluluk sağlamak.
3. OpenAPI taslağını doğrulanmış API dokümanına dönüştürmek.
