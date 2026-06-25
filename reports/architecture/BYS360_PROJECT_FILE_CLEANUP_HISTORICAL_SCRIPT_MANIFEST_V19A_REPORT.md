# BYS360 Project File Cleanup Historical Script Manifest V19A
- Generated at: 2026-06-25T18:14:46
- OK: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: ca08051
- Source report: reports/architecture/BYS360_POST_WAVE2_ACTIVE_RUNTIME_SCRIPT_DEFINITION_V17_REPORT.json
- Current script candidates: 290
- Strict active runtime script count: 48
- Required keep count: 180
- Historical candidate count: 86

## Historical Decision Counts
- historical_archive_candidate: 2
- historical_review_candidate: 21
- unreferenced_review_candidate: 63

## Projection
- after_wave3_safe: 288
- after_wave3_safe_and_review: 267
- after_all_historical_review: 204
- strict_active_runtime_remains_under_100: True

## Archive Wave3 Safe
- scripts/communication/seed_corporate_information_center_recipients_v3_0_phase2_1.py: 152 lines | Tarihsel script klasorunde ve tarihsel/onarim ismi tasiyor.
- scripts/quality/bys360_s0e_reports_quality_backup_archive_cleanup.py: 663 lines | Tarihsel script klasorunde ve tarihsel/onarim ismi tasiyor.

## Archive Wave3 Review
- scripts/communication/seed_daily_mail_pilot_recipients_v1_1.py: 125 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/communication/seed_daily_mail_pilot_recipients_v1_2.py: 111 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/quality/bys360_a10d_hard_ui_precision_decision.py: 199 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/quality/bys360_a10e_hard_ui_false_positive_close.py: 152 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/quality/bys360_a10q_compat_wrapper_rename_apply.py: 336 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py: 423 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/quality/bys360_mobile_behavior_smoke_p2b.py: 431 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/quality/bys360_mobile_domain_smoke_p1f.py: 309 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/quality/bys360_mobile_request_level_smoke_p2c.py: 457 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/quality/bys360_s0f3_pytest_isolated_update_verify.py: 487 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/security/build_bys360_secure_release_v1_3.py: 144 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/security/build_bys360_secure_release_v1_4.py: 130 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/security/check_bys360_live_logout_force_clear_v2_13_3.py: 82 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/security/check_bys360_live_logout_force_clear_v2_13_4.py: 103 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/security/check_bys360_p0_security_observability_v1.py: 133 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/security/check_bys360_p0_sentry_dbssl_csp_v2.py: 183 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/security/check_bys360_p1_risk_hardening_v1.py: 80 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/security/check_bys360_secure_release_secret_clean_v1_3.py: 137 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/security/check_bys360_secure_release_secret_clean_v1_4.py: 116 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/security/check_bys360_secure_release_secret_clean_v1_5.py: 98 lines | Tarihsel script klasorunde ancak isim sinyali zayif.
- scripts/security/check_bys360_session_timeout_security_v1.py: 44 lines | Tarihsel script klasorunde ancak isim sinyali zayif.

## Archive Wave4 Unreferenced Review
- scripts/admin/check_system_admin_email_v2_16_0.py: 103 lines | Referans yok; manuel inceleme gerekir.
- scripts/admin/check_system_admin_email_v2_16_1_checkfix.py: 110 lines | Referans yok; manuel inceleme gerekir.
- scripts/apply_bys360_corporate_portal_v1.py: 93 lines | Referans yok; manuel inceleme gerekir.
- scripts/bys360_mobile_v2_8_73_quality_router_fcm_tests.py: 191 lines | Referans yok; manuel inceleme gerekir.
- scripts/check_bys360_compileall_legacy_script_syntax_v2_13_3.py: 40 lines | Referans yok; manuel inceleme gerekir.
- scripts/check_bys360_feedback_campaign_form_v2_13_2.py: 56 lines | Referans yok; manuel inceleme gerekir.
- scripts/check_bys360_feedback_left_menu_fix_v2_13_1.py: 64 lines | Referans yok; manuel inceleme gerekir.
- scripts/check_bys360_portal_instagram_full_hide_v2_11_8.py: 84 lines | Referans yok; manuel inceleme gerekir.
- scripts/check_bys360_portal_instagram_hide_v2_11_7.py: 66 lines | Referans yok; manuel inceleme gerekir.
- scripts/executive/check_executive_summary_advanced_v2_14_20.py: 35 lines | Referans yok; manuel inceleme gerekir.
- scripts/executive/check_executive_summary_advanced_v2_14_21.py: 61 lines | Referans yok; manuel inceleme gerekir.
- scripts/executive/fix_executive_summary_blueprint_indent_v2_14_4.py: 79 lines | Referans yok; manuel inceleme gerekir.
- scripts/executive/fix_send_daily_executive_summary_indent_v1_0_2.py: 181 lines | Referans yok; manuel inceleme gerekir.
- scripts/executive/fix_send_daily_executive_summary_indent_v1_0_3.py: 288 lines | Referans yok; manuel inceleme gerekir.
- scripts/executive/patch_register_executive_summary.py: 55 lines | Referans yok; manuel inceleme gerekir.
- scripts/executive/probe_exec_summary_routes_v1_3_3.py: 24 lines | Referans yok; manuel inceleme gerekir.
- scripts/executive/repair_exec_summary_daily_mail_tasks_v1_3_2_force_template.py: 77 lines | Referans yok; manuel inceleme gerekir.
- scripts/executive/repair_executive_summary_daily_mail_tasks_v1_3.py: 177 lines | Referans yok; manuel inceleme gerekir.
- scripts/local_check_cic_v4_0_user_columns.py: 16 lines | Referans yok; manuel inceleme gerekir.
- scripts/local_emergency_cic_v4_0_schema_patch.py: 33 lines | Referans yok; manuel inceleme gerekir.
- scripts/local_fix_cic_v4_0_schema_patch.py: 17 lines | Referans yok; manuel inceleme gerekir.
- scripts/menu/check_executive_summary_menu_v2_14_9.py: 57 lines | Referans yok; manuel inceleme gerekir.
- scripts/menu/check_executive_summary_native_menu_v2_14_19.py: 88 lines | Referans yok; manuel inceleme gerekir.
- scripts/performance/check_bys360_performance_completion_phase12_final_gate.py: 189 lines | Referans yok; manuel inceleme gerekir.
- scripts/performance/check_bys360_performance_v2_1_1_rule_engine_settings.py: 24 lines | Referans yok; manuel inceleme gerekir.
- scripts/performance/check_bys360_performance_v2_1_2_personnel_category.py: 22 lines | Referans yok; manuel inceleme gerekir.
- scripts/performance/check_bys360_performance_v2_1_3_personnel_category_card.py: 22 lines | Referans yok; manuel inceleme gerekir.
- scripts/performance/check_bys360_performance_v2_1_3a_personnel_category_sidebar.py: 60 lines | Referans yok; manuel inceleme gerekir.
- scripts/performance/check_bys360_performance_v2_1_4_category_scope_visibility.py: 19 lines | Referans yok; manuel inceleme gerekir.
- scripts/performance/check_bys360_performance_v2_1_5_category_period_scope.py: 19 lines | Referans yok; manuel inceleme gerekir.
- scripts/performance/check_bys360_performance_v2_1_6_category_period_integration.py: 11 lines | Referans yok; manuel inceleme gerekir.
- scripts/performance/check_bys360_performance_v2_1_6a_corporate_ui_category_delete.py: 29 lines | Referans yok; manuel inceleme gerekir.
- scripts/performance/repair_bys360_performance_completion_phase9_development_guidance_center_v1a_hotfix.py: 166 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_bys360_portal_experience_v1.py: 59 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_bys360_portal_experience_v1b.py: 22 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_bys360_portal_experience_v2b_feed_first.py: 54 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_bys360_portal_experience_v2c_post_cards.py: 66 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_bys360_portal_experience_v2d1_profile_visual_fix.py: 83 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_bys360_portal_experience_v2d_profile_area.py: 76 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_bys360_portal_experience_v2f_news_left.py: 47 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_bys360_portal_experience_v3a2_news_hardening.py: 49 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_bys360_portal_experience_v3a_press_news.py: 45 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_bys360_portal_experience_v3b2_social_auto_import.py: 31 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_bys360_portal_experience_v3b3_social_import_center.py: 28 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_bys360_portal_experience_v3b4_social_auto_flow_fix.py: 39 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_bys360_portal_experience_v3b5_app_task_control.py: 30 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_bys360_portal_experience_v3b_social_posts.py: 32 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_portal_interaction_permissions_v2_12_2.py: 46 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/check_portal_role_matrix_deep_v2_12_3.py: 70 lines | Referans yok; manuel inceleme gerekir.
- scripts/portal/seed_portal_interaction_permissions_v2_12_2.py: 71 lines | Referans yok; manuel inceleme gerekir.
- scripts/refactor/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_apply.py: 92 lines | Referans yok; manuel inceleme gerekir.
- scripts/refactor/bys360_mobile_routes_domain_split_p1c.py: 350 lines | Referans yok; manuel inceleme gerekir.
- scripts/refactor/bys360_mobile_routes_domain_split_p1d.py: 412 lines | Referans yok; manuel inceleme gerekir.
- scripts/refactor/bys360_mobile_routes_personnel_kpi_split_p1e.py: 381 lines | Referans yok; manuel inceleme gerekir.
- scripts/refactor/bys360_mobile_routes_shared_split_p1b.py: 242 lines | Referans yok; manuel inceleme gerekir.
- scripts/refactor/bys360_route_architecture_inventory_p1a.py: 366 lines | Referans yok; manuel inceleme gerekir.
- scripts/repo_hygiene/repair_bys360_repo_hygiene_p19c_cic_template_contract_wiring_v1.py: 386 lines | Referans yok; manuel inceleme gerekir.
- scripts/repo_hygiene/repair_bys360_repo_hygiene_p19c_cic_template_contract_wiring_v2.py: 370 lines | Referans yok; manuel inceleme gerekir.
- scripts/repo_hygiene/repair_bys360_repo_hygiene_p19c_cic_template_contract_wiring_v3.py: 429 lines | Referans yok; manuel inceleme gerekir.
- scripts/repo_hygiene/repair_bys360_repo_hygiene_p8_cic_template_service_migration_v1.py: 126 lines | Referans yok; manuel inceleme gerekir.
- scripts/run_bys360_instagram_portal_sync_v2_11_0.py: 11 lines | Referans yok; manuel inceleme gerekir.
- scripts/run_bys360_instagram_portal_sync_v2_11_2.py: 9 lines | Referans yok; manuel inceleme gerekir.
- scripts/scheduled/run_cic_auto_scheduler.py: 34 lines | Referans yok; manuel inceleme gerekir.

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- nginx_or_backup_created: False

## Decision
- Bu rapor dosya tasimaz ve silmez.
- Canli/Nginx/backup kapsami disindadir; yalnizca proje dosyasi temizligi icin manifest uretir.
- archive_wave3_safe bir sonraki guvenli arsiv dalgasi icin en dar listedir.
- review listeleri manuel onay olmadan tasinmamalidir.
