# BYS360 Post Phase4J Master Checklist V13 Report
- Generated at: 2026-06-25T16:42:38
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 9f006fb
- Phase4J tag: phase4j-ops-routes-split-pass-20260625
- Git status clean: False

## Counts
- python_files: 1688
- ps1_files: 54
- total_py_ps1: 1742
- large_py_500_plus_count: 122

## Checklist
- 0. .env git gecmisinden temizle: **needs_manual_verification**
- 1. DEPLOYMENT.md + BACKUP runbook: **found**
- 2. SECURITY.md KVKK politikasi: **found**
- 3. CONTRIBUTING.md onboarding bolumu: **found**
- 4. Integration testleri auth + performans: **found**
- 5. CI'a integration testleri ekle: **found**
- 6. God-object dosyalari bol: **partial_pass_ops_routes_done**
- 7. Aktif script sayisini 100 altina indir: **needs_more_work**
- 8. Nginx config ornegi + otomatik yedek: **missing_or_partial**
- 9. OpenAPI semasini tamamla: **found**

## Large Python Files 500+ Lines
- app/services/corporate_information_center.py: 2353 lines
- app/services/settings/effective_menu.py: 2132 lines
- app/menu_registry.py: 1567 lines
- app/services/performance/low_score_process_service.py: 1529 lines
- scripts/quality/bys360_score100_quality_gate_v1.py: 1340 lines
- app/services/ai_agent/service.py: 1336 lines
- app/services/settings/catalog.py: 1331 lines
- app/institutional/hr_personnel_operations_routes.py: 1243 lines
- app/main_handlers/account_communication_helpers.py: 1234 lines
- app/admin/ai_routes.py: 1202 lines
- app/support/routes.py: 1168 lines
- app/api/mobile/performance_routes.py: 1164 lines
- app/admin/routes.py: 1149 lines
- app/performance/engagement_feedback_routes.py: 1135 lines
- app/communication/surveys_routes.py: 1072 lines
- app/workflow/routes.py: 1065 lines
- app/support/help_center_content.py: 1058 lines
- app/services/ai/dashboard_panel_personnel.py: 1039 lines
- app/services/performance/process_engine_phase6_president_approvals.py: 1015 lines
- app/portal/routes.py: 997 lines
- app/models/hr_models.py: 995 lines
- app/main_handlers/account_settings_helpers.py: 972 lines
- app/services/ai/dashboard_panel_repository.py: 965 lines
- app/services/feedback_service.py: 916 lines
- app/services/dashboard_rebuild_service.py: 898 lines
- app/services/ai_agent/assistant_full_stepwise_tutor_v5.py: 887 lines
- app/services/hr_operations_service.py: 881 lines
- app/services/communication_phase2_service.py: 875 lines
- app/services/ai_agent/assistant_chatgpt_like_v31.py: 870 lines
- app/performance/phase10_development_guidance_ui.py: 867 lines

## Recommendation
- Phase4J ops_routes split tamamlandi ve taglendi.
- Ana listede siradaki net teknik hedef aktif script sayisini dusurmek veya integration/CI kanitlarini sertlestirmektir.
- large_py_500_plus listesi kalan god-object adaylarini gosterir.
