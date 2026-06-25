# BYS360 Project File Cleanup Review Candidates Deep Classification V20A
- Generated at: 2026-06-25T18:22:33
- OK: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 3d827e7
- Source report: reports/architecture/BYS360_PROJECT_FILE_CLEANUP_HISTORICAL_SCRIPT_MANIFEST_V19A_REPORT.json
- Review candidate count: 84

## Decision Counts
- archive_wave4_safe: 15
- archive_wave5_review: 1
- keep_risk_review: 68

## Projection
- current_active_script_candidates: 288
- archive_wave4_safe_count: 15
- archive_wave5_review_count: 1
- projected_after_wave4_safe: 273
- projected_after_wave4_safe_and_wave5_review: 272

## Archive Wave4 Safe
- scripts/security/check_bys360_session_timeout_security_v1.py: 44 lines | Tarihsel klasorde, guvenli kalite/rapor/kanit markerlari var ve risk marker yok.
- scripts/admin/check_system_admin_email_v2_16_1_checkfix.py: 110 lines | Referanssiz ve kalite/rapor/kanit niteliginde; risk marker yok.
- scripts/check_bys360_portal_instagram_full_hide_v2_11_8.py: 84 lines | Referanssiz ve kalite/rapor/kanit niteliginde; risk marker yok.
- scripts/check_bys360_portal_instagram_hide_v2_11_7.py: 66 lines | Referanssiz ve kalite/rapor/kanit niteliginde; risk marker yok.
- scripts/executive/check_executive_summary_advanced_v2_14_20.py: 35 lines | Referanssiz ve kalite/rapor/kanit niteliginde; risk marker yok.
- scripts/executive/check_executive_summary_advanced_v2_14_21.py: 61 lines | Referanssiz ve kalite/rapor/kanit niteliginde; risk marker yok.
- scripts/menu/check_executive_summary_menu_v2_14_9.py: 57 lines | Referanssiz ve kalite/rapor/kanit niteliginde; risk marker yok.
- scripts/menu/check_executive_summary_native_menu_v2_14_19.py: 88 lines | Referanssiz ve kalite/rapor/kanit niteliginde; risk marker yok.
- scripts/portal/check_bys360_portal_experience_v2b_feed_first.py: 54 lines | Referanssiz ve kalite/rapor/kanit niteliginde; risk marker yok.
- scripts/portal/check_bys360_portal_experience_v2c_post_cards.py: 66 lines | Referanssiz ve kalite/rapor/kanit niteliginde; risk marker yok.
- scripts/portal/check_bys360_portal_experience_v2d1_profile_visual_fix.py: 83 lines | Referanssiz ve kalite/rapor/kanit niteliginde; risk marker yok.
- scripts/portal/check_bys360_portal_experience_v2d_profile_area.py: 76 lines | Referanssiz ve kalite/rapor/kanit niteliginde; risk marker yok.
- scripts/portal/check_bys360_portal_experience_v2f_news_left.py: 47 lines | Referanssiz ve kalite/rapor/kanit niteliginde; risk marker yok.
- scripts/portal/check_bys360_portal_experience_v3b3_social_import_center.py: 28 lines | Referanssiz ve kalite/rapor/kanit niteliginde; risk marker yok.
- scripts/refactor/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_apply.py: 92 lines | Referanssiz ve kalite/rapor/kanit niteliginde; risk marker yok.

## Archive Wave5 Review
- scripts/executive/patch_register_executive_summary.py: 55 lines | Referanssiz ama guvenli tarihsel marker zayif; manuel onay gerekir.

## Keep Review
- scripts/communication/seed_daily_mail_pilot_recipients_v1_1.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/communication/seed_daily_mail_pilot_recipients_v1_2.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/quality/bys360_a10d_hard_ui_precision_decision.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/quality/bys360_a10e_hard_ui_false_positive_close.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/quality/bys360_a10q_compat_wrapper_rename_apply.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/quality/bys360_mobile_behavior_smoke_p2b.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/quality/bys360_mobile_domain_smoke_p1f.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/quality/bys360_mobile_request_level_smoke_p2c.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/quality/bys360_s0f3_pytest_isolated_update_verify.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/security/build_bys360_secure_release_v1_3.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/security/build_bys360_secure_release_v1_4.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/security/check_bys360_live_logout_force_clear_v2_13_3.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/security/check_bys360_live_logout_force_clear_v2_13_4.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/security/check_bys360_p0_security_observability_v1.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/security/check_bys360_p0_sentry_dbssl_csp_v2.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/security/check_bys360_p1_risk_hardening_v1.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/security/check_bys360_secure_release_secret_clean_v1_3.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/security/check_bys360_secure_release_secret_clean_v1_4.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/security/check_bys360_secure_release_secret_clean_v1_5.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/admin/check_system_admin_email_v2_16_0.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/apply_bys360_corporate_portal_v1.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/bys360_mobile_v2_8_73_quality_router_fcm_tests.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/check_bys360_compileall_legacy_script_syntax_v2_13_3.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/check_bys360_feedback_campaign_form_v2_13_2.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/check_bys360_feedback_left_menu_fix_v2_13_1.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/executive/fix_executive_summary_blueprint_indent_v2_14_4.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/executive/fix_send_daily_executive_summary_indent_v1_0_2.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/executive/fix_send_daily_executive_summary_indent_v1_0_3.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/executive/probe_exec_summary_routes_v1_3_3.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/executive/repair_exec_summary_daily_mail_tasks_v1_3_2_force_template.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/executive/repair_executive_summary_daily_mail_tasks_v1_3.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/local_check_cic_v4_0_user_columns.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/local_emergency_cic_v4_0_schema_patch.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/local_fix_cic_v4_0_schema_patch.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/performance/check_bys360_performance_completion_phase12_final_gate.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/performance/check_bys360_performance_v2_1_1_rule_engine_settings.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/performance/check_bys360_performance_v2_1_2_personnel_category.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/performance/check_bys360_performance_v2_1_3_personnel_category_card.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/performance/check_bys360_performance_v2_1_3a_personnel_category_sidebar.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/performance/check_bys360_performance_v2_1_4_category_scope_visibility.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/performance/check_bys360_performance_v2_1_5_category_period_scope.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/performance/check_bys360_performance_v2_1_6_category_period_integration.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/performance/check_bys360_performance_v2_1_6a_corporate_ui_category_delete.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/performance/repair_bys360_performance_completion_phase9_development_guidance_center_v1a_hotfix.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/portal/check_bys360_portal_experience_v1.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/portal/check_bys360_portal_experience_v1b.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/portal/check_bys360_portal_experience_v3a2_news_hardening.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/portal/check_bys360_portal_experience_v3a_press_news.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/portal/check_bys360_portal_experience_v3b2_social_auto_import.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/portal/check_bys360_portal_experience_v3b4_social_auto_flow_fix.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/portal/check_bys360_portal_experience_v3b5_app_task_control.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/portal/check_bys360_portal_experience_v3b_social_posts.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/portal/check_portal_interaction_permissions_v2_12_2.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/portal/check_portal_role_matrix_deep_v2_12_3.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/portal/seed_portal_interaction_permissions_v2_12_2.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/refactor/bys360_mobile_routes_domain_split_p1c.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/refactor/bys360_mobile_routes_domain_split_p1d.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/refactor/bys360_mobile_routes_personnel_kpi_split_p1e.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/refactor/bys360_mobile_routes_shared_split_p1b.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/refactor/bys360_route_architecture_inventory_p1a.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/repo_hygiene/repair_bys360_repo_hygiene_p19c_cic_template_contract_wiring_v1.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/repo_hygiene/repair_bys360_repo_hygiene_p19c_cic_template_contract_wiring_v2.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/repo_hygiene/repair_bys360_repo_hygiene_p19c_cic_template_contract_wiring_v3.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/repo_hygiene/repair_bys360_repo_hygiene_p8_cic_template_service_migration_v1.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/run_bys360_instagram_portal_sync_v2_11_0.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/run_bys360_instagram_portal_sync_v2_11_2.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.
- scripts/scheduled/run_cic_auto_scheduler.py: decision=keep_risk_review | Canli/DB/yedek/migration/silme gibi risk markerlari bulundu.

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- nginx_or_backup_created: False

## Decision
- Bu rapor dosya tasimaz ve silmez.
- Kalan 84 review adayini icerik ve risk markerlarina gore siniflandirir.
- archive_wave4_safe sonraki dar guvenli arsiv dalgasidir.
- archive_wave5_review ve keep_review listeleri manuel onay olmadan tasinmamalidir.
