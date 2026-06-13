# BYS360 STATUS


<!-- PHASE2C6_STATUS_20260613 -->

## 2026-06-13 - Faz 2C6 Wildcard Import Durum Kararı

### Durum

Faz 2C5 sonunda düşük riskli wildcard import temizliği kontrollü şekilde uygulanmıştır.

- C5 aday sayısı: 5
- Kalıcı tutulan değişiklik: 4
- Güvenli geri alınan değişiklik: 1
- App AST wildcard sayısı: 62 -> 58
- Final test sonucu: 746 passed, 2 skipped, 34 deselected, 0 failed, 0 errors, 0 warnings
- Rollback all performed: False

### Kalıcı Temizlenen Dosyalar

- app/institutional/hr_form_helpers.py
- app/institutional/hr_reports_routes.py
- app/institutional/routes.py - app.institutional.hr_common importu
- app/institutional/routes.py - app.institutional.hr_personnel_operations_routes importu

### Güvenli Geri Alınan Dosya

- app/institutional/hr_scope_helpers.py

Gerekçe: açık import denemesi uygulama başlangıcında _safe_import bağımlılığı üzerinden test kırılımı oluşturduğu için dosya güvenli şekilde eski haline döndürülmüştür.

### Karar

Faz 2C6 kapsamında kalan wildcard importlar artık otomatik toplu temizlik konusu değildir. Kalanlar şu şekilde ele alınacaktır:

1. Güvenli ve küçük olanlar ileride mevcut modül düzenlemesi sırasında temizlenecek.
2. Facade/aggregator dosyaları bilinçli istisna olarak tutulacak.
3. Riskli dosyalar ayrı refactor konusu yapılacak.
4. Yeni script, yeni README, yeni manifest üretme alışkanlığı bırakılacaktır.
5. Bundan sonraki değişiklikler mevcut modül, mevcut test ve mevcut doküman üzerinden ilerleyecektir.

### Sonraki Adım

Faz 2Z final kapanış: compileall, route contract, auth guard, quality smoke, default pytest ve doküman kararlarının birlikte doğrulanması.


<!-- PHASE2Y_ROOT_DOC_ARCHIVE_20260613 -->

## 2026-06-13 12:09:35 - Faz 2Y-1 Kök Dizin Doküman Sadeleştirme

Kök dizindeki eski SAFE/HOTFIX/MANIFEST odaklı geçici dokümanlar docs/archive/legacy-root/ altına taşındı.

Amaç:

- Kök dizini sadeleştirmek
- Güncel durum bilgisini STATUS.md içinde toplamak
- Güncel mimari bilgiyi ARCHITECTURE.md içinde toplamak
- Yeni README / manifest üretme alışkanlığını bırakmak

Bu adımda uygulama koduna dokunulmadı.

<!-- PHASE2Y_QUALITY_ARCHIVE_WAVE1_20260613 -->

## 2026-06-13 13:15:56 - Faz 2Y-3 scripts/quality Arşiv Dalgası 1

scripts/quality/ içindeki referanssız eski repair/check/apply/analyze tarzı kalite yardımcılarının ilk dalgası arşive taşındı.

- Toplam kalite script sayısı: 374
- Referanssız eski tarz aday sayısı: 254
- Bu dalgada arşive taşınan dosya sayısı: 120
- Arşiv hedefi: scripts/archive/quality/phase2y-wave1/

Bu adımda uygulama koduna, test davranışına, migration dosyalarına veya canlı ortama dokunulmadı.

Arşive alınan ilk dalga:

- analyze_bys360_mobile_route_split_p1_1_v2_17_6.py
- analyze_p11_b_mobile_routes_inventory_v1.py
- analyze_p11_b1_mobile_routes_split_candidates_v1.py
- analyze_p11_b1a_mobile_routes_split_candidates_v1.py
- analyze_p11_b8_mobile_routes_remaining_refresh_v1.py
- analyze_p11_c_mobile_performance_routes_inventory_v1.py
- analyze_p11_c2_mobile_performance_routes_remaining_refresh_v1.py
- analyze_p11_d_menu_registry_inventory_v1.py
- analyze_p11_d1_menu_registry_data_candidates_v1.py
- analyze_p11_e_effective_menu_inventory_v1.py
- analyze_p11_e1_effective_menu_dependency_candidates_v1.py
- analyze_p11_f_settings_template_inventory_v1.py
- analyze_p11_g_evaluation_template_inventory_v1.py
- analyze_p11_g1_evaluation_safe_split_candidates_v1.py
- analyze_p11_h_css_inventory_v1.py
- analyze_p12_a_technical_ui_term_inventory_v1.py
- analyze_p12_a1_technical_ui_term_inventory_fix_v1.py
- analyze_p12_b_technical_ui_term_decision_v1.py
- analyze_p13_a_effective_p1_closure_map_v1.py
- analyze_p13_a2_effective_p1_closure_map_corrected_v1.py
- analyze_p13_a3_effective_p1_closure_from_p7_v1.py
- analyze_p13_b_repair_script_inventory_v1.py
- analyze_p13_c_repair_script_archive_dryrun_v1.py
- analyze_p14_a_assistant_js_inventory_v1.py
- analyze_p14_b_assistant_js_split_decision_v1.py
- analyze_p14_c_assistant_js_helper_split_dryrun_v1.py
- analyze_p14_d_assistant_js_split_readiness_v1.py
- analyze_p14_f_assistant_js_split_verification_v1.py
- analyze_p14_i_final_closure_report_v1.py
- analyze_quality_findings_by_level_v1.py
- analyze_technical_ui_terms_v1.py
- apply_exact_line_silent_except_v1.py
- apply_mobile_internal_naming_v1.py
- apply_next_simple_silent_except_target_v1.py
- apply_p1_except_without_log_v1.py
- apply_p11_b2_mobile_utility_routes_bridge_v1.py
- apply_p11_b3_mobile_light_read_routes_bridge_v1.py
- apply_p11_b4_mobile_detail_read_routes_bridge_v1.py
- apply_p11_b5_mobile_support_survey_read_routes_bridge_v1.py
- apply_p11_b6_mobile_communication_read_routes_bridge_v1.py
- apply_p11_b7_mobile_communication_v2_read_route_bridge_v1.py
- apply_p11_b9_mobile_performance_read_routes_bridge_v1.py
- apply_p11_c1_mobile_performance_read_routes_bridge_v1.py
- apply_p11_d2_menu_registry_safe_data_bridge_v1.py
- apply_p11_d3_menu_sections_bridge_v1.py
- apply_p11_f1_settings_style_partial_v1.py
- apply_p11_g2_evaluation_style_partial_v1.py
- apply_p11_h1_css_wrapper_split_v1.py
- apply_p13_e_analysis_script_p0_fix_v1.py
- apply_p13_e2_p12b_last_p0_fix_v1.py
- apply_p13_f_repair_inventory_except_log_fix_v1.py
- apply_p13_f2_repair_inventory_logger_fix_v1.py
- apply_p13_f3_repair_inventory_force_logging_fix_v1.py
- apply_p14_e_assistant_js_helper_split_apply_v1.py
- apply_p14_e2_assistant_js_helper_split_safe_apply_v1.py
- apply_p14f1_mobile_api_blueprint_name_fix_v1.py
- apply_p14f2_mobile_api_route_registrar_adapter_v1.py
- apply_safe_remaining_tech_naming_v1.py
- apply_single_block_silent_except_v1.py
- apply_technical_ui_safe_false_positive_v1.py
- apply_technical_ui_safe_text_v1.py
- bys360_mobile_refactor_closure_inventory_p1_10_v2_17_20.py
- bys360_mobile_service_scaffold_p1_2_v2_17_7.py
- bys360_quality_audit_v1.py
- bys360_repo_hygiene_p0_1_compile_fix_v2_17_1.py
- bys360_repo_hygiene_p0_2_active_audit_health_v2_17_2.py
- bys360_repo_hygiene_p0_2_active_audit_health_v2_17_3.py
- bys360_repo_hygiene_p0_3_duplicate_tree_cleanup_v2_17_4.py
- bys360_route_refactor_inventory_p1_v2_17_5.py
- check_bys360_cic_v3_0_auto_mail_weekday_only_v1.py
- check_bys360_cic_v3_0_live_final_release_resume_v5_direct_stable.py
- check_bys360_cic_v3_0_live_final_release_resume_v6_lock_safe.py
- check_bys360_cic_v3_0_mail_engine_system_sender_v1.py
- check_bys360_cic_v3_0_mail_engine_system_sender_v1_1.py
- check_bys360_cic_v3_0_recipients_pro_usability_v1.py
- check_bys360_cic_v3_0_recipients_save_persistence_v2.py
- check_bys360_cic_v3_0_recipients_save_persistence_v2_1_gate_fix.py
- check_bys360_cic_v3_0_system_auto_mail_scheduler_v1.py
- check_bys360_corporate_portal_maturity_v1_6.py
- check_bys360_corporate_portal_media_video_v2_3.py
- check_bys360_csrf_main_login_hotfix_v2_15_14.py
- check_bys360_home_festival_portal_v2_5.py
- check_bys360_home_festival_portal_v2_5_1.py
- check_bys360_home_portal_safe_links_v2_7.py
- check_bys360_portal_composer_accordion_v2_6.py
- check_bys360_portal_delete_route_dedupe_v2_10_1.py
- check_bys360_portal_delete_route_dedupe_v2_10_2.py
- check_bys360_portal_iphone_responsive_v2_11.py
- check_bys360_portal_media_comments_mentions_v2_12_1.py
- check_bys360_portal_people_premium_v2_10.py
- check_bys360_portal_profile_me_link_v2_10_3.py
- check_bys360_portal_profile_me_link_v2_10_4.py
- check_bys360_portal_profile_me_link_v2_10_5.py
- check_bys360_portal_profile_me_link_v2_10_6.py
- check_bys360_portal_profile_me_link_v2_10_7.py
- check_bys360_portal_profile_wall_v2_8.py
- check_bys360_portal_profile_wall_v2_8_1.py
- check_bys360_portal_profile_wall_v2_9.py
- check_bys360_portal_profile_wall_v2_9_1.py
- check_bys360_portal_profile_wall_v2_9_2.py
- check_bys360_portal_profile_wall_v2_9_3.py
- check_bys360_portal_profile_wall_v2_9_4.py
- check_bys360_portal_profile_wall_v2_9_5.py
- check_bys360_portal_settings_role_matrix_v2_12.py
- check_corporate_information_center_v3_0_phase1.py
- check_corporate_information_center_v3_0_phase2.py
- check_corporate_information_center_v3_0_phase2_1.py
- check_corporate_information_center_v3_0_phase2_3.py
- check_corporate_information_center_v3_0_phase4_1_real_advanced_ui.py
- check_corporate_information_center_v3_0_phase4_advanced_ui.py
- check_corporate_information_center_v3_0_phase5_2_flat_gate_fix.py
- check_corporate_information_center_v3_0_phase6_1_staff_noon_message.py
- check_corporate_information_center_v3_0_phase7_1_base_css_link_fix.py
- check_corporate_information_center_v3_0_phase7_10_status_pill_fix.py
- check_corporate_information_center_v3_0_phase7_11_template_compat_fix.py
- check_corporate_information_center_v3_0_phase7_3_flat_css_link_fix.py
- check_corporate_information_center_v3_0_phase7_7_release_clean_ui.py
- check_corporate_information_center_v3_0_phase7_8_base_header_pro.py
- check_corporate_information_center_v3_0_phase7_live_release_usage.py
- check_daily_mail_pilot_v1_1.py


<!-- PHASE2Y_QUALITY_ARCHIVE_WAVE2_20260613 -->

## 2026-06-13 13:30:22 - Faz 2Y-4 scripts/quality Arşiv Dalgası 2

scripts/quality/ içindeki kalan referanssız eski repair/check/apply/analyze tarzı kalite yardımcıları ikinci dalgada arşive taşındı.

- Wave1 sonrası kalan scripts/quality sayısı: 254
- Bu dalgada arşive taşınan dosya sayısı: 135
- Arşiv hedefi: scripts/archive/quality/phase2y-wave2/

Bu adımda uygulama koduna, test davranışına, migration dosyalarına veya canlı ortama dokunulmadı. Referans alan kalite kapıları korunmuştur.

Arşive alınan ikinci dalga:

- check_corporate_information_center_v3_0_phase5_1_gate_fix.py
- check_daily_mail_pilot_v1_2.py
- check_daily_mail_tasks_v1_4.py
- check_daily_weather_mail_v1_0.py
- check_daily_weather_mail_v1_0_4_executive_summary.py
- check_daily_weather_mail_v1_0_5.py
- check_daily_weather_mail_v1_0_6.py
- check_daily_weather_mail_v1_0_7_system_admin_only.py
- check_exec_summary_daily_mail_tasks_v1_3_2.py
- check_exec_summary_daily_mail_tasks_v1_3_4.py
- check_exec_summary_daily_mail_tasks_v1_3_5.py
- check_executive_mail_center_v1_5.py
- check_executive_mail_center_v1_6.py
- check_executive_mail_center_v2_0.py
- check_executive_summary_admin_only_v1_0_10.py
- check_executive_summary_daily_mail_tasks_v1_3.py
- check_executive_summary_daily_mail_tasks_v1_3_1.py
- check_executive_summary_v1_0_8_admin_professional.py
- check_executive_summary_v3_local_pro_ui.py
- check_p14_g_p0_silent_except_fix_v1.py
- check_p14_g2_self_p0_fix_v1.py
- check_p14_h_p1_cleanup_v1.py
- check_p14_h2_self_except_fix_v1.py
- check_p14f1_mobile_api_blueprint_name_fix_v1.py
- check_p14f2_mobile_api_route_registrar_adapter_v1.py
- check_p14f4_source_aware_existing_assistant_v1.py
- check_p14j_performance_archive_template_v1.py
- check_p14j2_performance_archive_corporate_template_v1.py
- decide_remaining_p1_final_v1.py
- filter_bys360_quality_audit_exclude_backups_v1.py
- find_next_simple_silent_except_targets_v1.py
- plan_p11_refactor_v1.py
- repair_bys360_mobile_assistant_handler_delegate_p1_9_v2_17_19.py
- repair_bys360_mobile_auth_service_delegate_p1_3_v2_17_8.py
- repair_bys360_mobile_auth_service_delegate_p1_3b_v2_17_9.py
- repair_bys360_mobile_authenticated_performance_get_smoke_p3_9_fix_v2_17_47.py
- repair_bys360_mobile_communication_handler_delegate_p1_8_v2_17_18.py
- repair_bys360_mobile_dashboard_profile_delegate_p1_4_v2_17_10.py
- repair_bys360_mobile_dashboard_profile_delegate_p1_4c_v2_17_12.py
- repair_bys360_mobile_performance_development_delegate_p2_6_v2_17_31.py
- repair_bys360_mobile_performance_full_summary_delegate_p2_2_v2_17_26.py
- repair_bys360_mobile_performance_history_delegate_p2_3b_v2_17_28.py
- repair_bys360_mobile_performance_p3_helper_closure_smoke_v2_17_43.py
- repair_bys360_mobile_performance_period_detail_delegate_p3_7_v2_17_41.py
- repair_bys360_mobile_performance_period_detail_delegate_p3_7b_v2_17_42.py
- repair_bys360_mobile_performance_period_notes_read_delegate_p3_6_v2_17_40.py
- repair_bys360_mobile_performance_refactor_closure_p2_7_v2_17_32.py
- repair_bys360_mobile_performance_reports_delegate_p2_3_v2_17_27.py
- repair_bys360_mobile_performance_reports_single_delegate_p2_4_v2_17_29.py
- repair_bys360_mobile_performance_risk_single_delegate_p2_5_v2_17_30.py
- repair_bys360_mobile_performance_score_form_helper_delegate_p3_2_v2_17_36.py
- repair_bys360_mobile_performance_smoke_500_fix_v2_17_48.py
- repair_bys360_mobile_performance_smoke_500_force_safe_v2_17_49.py
- repair_bys360_mobile_performance_smoke_test_p2_8_v2_17_33.py
- repair_bys360_mobile_performance_summary_delegate_p2_1_v2_17_25.py
- repair_bys360_mobile_performance_write_route_plan_p3_v2_17_34.py
- repair_bys360_mobile_performance_write_smoke_precheck_p3_1_v2_17_35.py
- repair_bys360_mobile_personnel_handler_delegate_p1_7_v2_17_17.py
- repair_bys360_mobile_smoke_baseline_p1_11_v2_17_21.py
- repair_bys360_mobile_support_service_delegate_p1_5_v2_17_13.py
- repair_bys360_mobile_support_service_delegate_p1_5b_v2_17_14.py
- repair_bys360_mobile_survey_handler_delegate_p1_6_v2_17_15.py
- repair_bys360_mobile_survey_handler_delegate_p1_6b_v2_17_16.py
- repair_bys360_mobile_urlmap_smoke_probe_p1_12_v2_17_23.py
- repair_bys360_quality_10_10_p1_silent_except_logging.py
- repair_bys360_sqlite_postgres_db_compat_v2_17_50.py
- repair_bys360_tech_debt_final_closure_v2_17_45.py
- repair_bys360_tech_debt_final_closure_v2_17_46.py
- repair_single_file_silent_except_v1.py
- triage_remaining_p1_v1.py
- repair_bys360_repo_hygiene_p1_v2_17_53.py
- repair_bys360_repo_hygiene_p1b_syntax_probe_v2_17_54.py
- check_cic_v4_0a_celebrations_menu_tab.py
- check_cic_v4_1b_force_pro_ui.py
- check_cic_v4_2_global_sidebar_cache_fix.py
- check_cic_v4_2b_active_passive_sidebar_fix.py
- check_cic_v4_2c_active_passive_hard_patch.py
- check_cic_v4_2d_active_passive_syntax_fix.py
- check_cic_v4_3_full_pro_ui_sidebar_active.py
- check_cic_v4_4_performance_style_reset.py
- check_cic_v4_4a_system_link_polish.py
- check_cic_v4_4b_system_page_final_polish.py
- check_cic_v4_5_celebration_excel_import.py
- check_cic_v4_5a_celebration_excel_import_lock_fix.py
- check_cic_v4_6a_jinja_slice_fix.py
- check_cic_v4_6b_celebrations_template_final_fix.py
- check_corporate_information_center_v3_0_phase2_2.py
- repair_bys360_mobile_performance_action_helpers_delegate_p3_3_v2_17_37.py
- repair_bys360_mobile_performance_period_note_helpers_delegate_p3_5_v2_17_39.py
- repair_bys360_mobile_performance_return_helpers_delegate_p3_4_v2_17_38.py
- repair_bys360_mobile_performance_route_split_plan_p2_v2_17_24.py
- repair_bys360_repo_hygiene_p4_big_file_modularization_audit_v1.py
- bys360_repo_hygiene_p0_v2_17_0.py
- bys360_ops_triage_v2.py
- bys360_print_cleanup_v3.py
- bys360_exception_triage_v4.py
- bys360_exception_guardrail_v5.py
- bys360_ops_exception_v6a_critical_cleanup.py
- bys360_ops_hardening_v6b_permission_session_auth.py
- bys360_ops_hardening_v6c_mail_notification_support.py
- bys360_ops_hardening_v6d_performance_critical_exception_cleanup.py
- repair_bys360_quality9_performance_hierarchy_logging_hotfix_v3.py
- repair_bys360_quality9_future_import_logging_order_hotfix_v4.py
- repair_bys360_quality9_future_docstring_syntax_hotfix_v6.py
- repair_bys360_quality9_future_docstring_syntax_hotfix_v7.py
- repair_bys360_quality9_future_docstring_syntax_hotfix_v8.py
- check_bys360_cic_logging_import_hotfix_v1.py
- check_bys360_cic_logging_order_hotfix_v2.py
- check_bys360_ios_responsive_completion_v1.py
- check_bys360_android_responsive_completion_v1.py
- repair_bys360_claude_score_uplift_p0b_secret_gate_precision_v1.py
- bys360_mobile_pytest_contract_gate_p2a_v2.py
- bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v2.py
- bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3.py
- bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py
- bys360_mobile_role_boundary_matrix_gate_p4b_v2.py
- bys360_mobile_role_boundary_matrix_gate_p4b_v3.py
- bys360_local_sqlite_persistent_db_hotfix_v2.py
- check_bys360_broad_except_ratchet_safe_v1.py
- bys360_f821_cleanup_safe_v1.py
- bys360_f821_cleanup_safe_v2.py
- bys360_a5_test_triage_safe_v1.py
- apply_p14_g_p0_silent_except_fix_v1.py
- apply_p14_g2_self_p0_fix_v1.py
- apply_p14_h_p1_cleanup_v1.py
- apply_p14_h2_self_except_fix_v1.py
- bys360_a10g_safe_cleanup_quarantine.py
- bys360_a10h_iterative_safe_cleanup.py
- bys360_s0c_config_secretkey_exc_hotfix.py
- bys360_s0c3_remaining_secretkey_block_hotfix.py
- bys360_s0d_pytest_config_backup_collection_hotfix.py
- bys360_phase2a_ruff_missing_hotfix.py
- bys360_phase2c2_comment_aware_hotfix.py
- bys360_phase2c2_safe_subset_mobile_shared_apply.py
- bys360_phase2c2z_safe_subset_final_verify.py


<!-- PHASE2Y_QUALITY_ARCHIVE_WAVE2_CORRECTION_20260613 -->

## 2026-06-13 13:34:50 - Faz 2Y-4 Düzeltme: Referanslı Gate Dosyaları Geri Alındı

İkinci arşiv dalgasında 135 dosya arşive taşındıktan sonra test koleksiyonunda 4 import hatası görüldü.

Geri alınan dosyalar:

- bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v2.py
- bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3.py
- bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py
- bys360_mobile_role_boundary_matrix_gate_p4b_v3.py

Karar:

- Bu dosyalar 	ests/architecture tarafından doğrudan import edildiği için aktif kalite gate kabul edildi.
- Wave2 net arşiv sayısı 135 değil, 131 olarak düzeltilmiştir.
- Aktif kalan scripts/quality sayısı 119 değil, 123 olarak kabul edilmelidir.
- Bu düzeltme uygulama koduna, migration dosyalarına veya canlı ortama dokunmamıştır.

