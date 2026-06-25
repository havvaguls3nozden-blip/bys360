# BYS360 Project File Cleanup Wave4 Safe Archive V20B
- Generated at: 2026-06-25T18:24:39
- OK: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD before report commit: fd241da
- Source report: reports/architecture/BYS360_PROJECT_FILE_CLEANUP_REVIEW_CANDIDATES_DEEP_CLASSIFICATION_V20A_REPORT.json
- Archive root: archive/scripts_retired_20260625_wave4
- Before active script candidates: 288
- After active script candidates: 273
- Expected after active script candidates: 273
- Manifest count: 15
- Moved count: 15
- Already archived count: 0
- Missing count: 0

## Moved Files
- scripts/security/check_bys360_session_timeout_security_v1.py -> archive/scripts_retired_20260625_wave4/scripts/security/check_bys360_session_timeout_security_v1.py | sha256=81499c52a4fca0f1e6c318eae5de747292c6f1f26a07f105216d63e0b73737ef
- scripts/admin/check_system_admin_email_v2_16_1_checkfix.py -> archive/scripts_retired_20260625_wave4/scripts/admin/check_system_admin_email_v2_16_1_checkfix.py | sha256=5cb34222fb43751f918f812de3ec9a909bc7ffd5839f682a52c8ed9e6d6841ea
- scripts/check_bys360_portal_instagram_full_hide_v2_11_8.py -> archive/scripts_retired_20260625_wave4/scripts/check_bys360_portal_instagram_full_hide_v2_11_8.py | sha256=48c024f31368a84bdcfd2d2362a517b4f84f3db64335797a6bf0c29f1a506d8b
- scripts/check_bys360_portal_instagram_hide_v2_11_7.py -> archive/scripts_retired_20260625_wave4/scripts/check_bys360_portal_instagram_hide_v2_11_7.py | sha256=a826f1f818e60fc35ceab201f91e293d3efdf13bb64df245fef6eee87f524d1e
- scripts/executive/check_executive_summary_advanced_v2_14_20.py -> archive/scripts_retired_20260625_wave4/scripts/executive/check_executive_summary_advanced_v2_14_20.py | sha256=1744557b762d7642836b3c4a0f75808fe2de9e70d5314aef6b25dc53bd45f445
- scripts/executive/check_executive_summary_advanced_v2_14_21.py -> archive/scripts_retired_20260625_wave4/scripts/executive/check_executive_summary_advanced_v2_14_21.py | sha256=9f4649b1f16022547c895b38315a93cf705a21697d719e244d3a3d7de219ade6
- scripts/menu/check_executive_summary_menu_v2_14_9.py -> archive/scripts_retired_20260625_wave4/scripts/menu/check_executive_summary_menu_v2_14_9.py | sha256=976eea0134c22a12aeae255113f7b7d77825bdf088c2b868cd9d9b9065132170
- scripts/menu/check_executive_summary_native_menu_v2_14_19.py -> archive/scripts_retired_20260625_wave4/scripts/menu/check_executive_summary_native_menu_v2_14_19.py | sha256=3af6a4a19f496679286b9344711cbd3921c5c3d32902cd4f98ea592f8cd21d46
- scripts/portal/check_bys360_portal_experience_v2b_feed_first.py -> archive/scripts_retired_20260625_wave4/scripts/portal/check_bys360_portal_experience_v2b_feed_first.py | sha256=0fbdf22f7bb437cc595bd81775d16a2917b6dcb7c61fd5fd032a2f7c4d3231df
- scripts/portal/check_bys360_portal_experience_v2c_post_cards.py -> archive/scripts_retired_20260625_wave4/scripts/portal/check_bys360_portal_experience_v2c_post_cards.py | sha256=fcbf69e151aaaaaea32d59358809dbbf2c10987a5a7c60b28844a5b16e0782c0
- scripts/portal/check_bys360_portal_experience_v2d1_profile_visual_fix.py -> archive/scripts_retired_20260625_wave4/scripts/portal/check_bys360_portal_experience_v2d1_profile_visual_fix.py | sha256=a050a3edb1286c43a483f121f9ab97c1f6bd52aa71d894600a60fb2cebad4c0f
- scripts/portal/check_bys360_portal_experience_v2d_profile_area.py -> archive/scripts_retired_20260625_wave4/scripts/portal/check_bys360_portal_experience_v2d_profile_area.py | sha256=ab5e0d73f8a5fdca540153dd5715cb0fc25df07c75de0d31ce96f20a1f908e80
- scripts/portal/check_bys360_portal_experience_v2f_news_left.py -> archive/scripts_retired_20260625_wave4/scripts/portal/check_bys360_portal_experience_v2f_news_left.py | sha256=0e299379f0cb5f35bb9463123664011f5108448db2452872e81d58d8f65a9267
- scripts/portal/check_bys360_portal_experience_v3b3_social_import_center.py -> archive/scripts_retired_20260625_wave4/scripts/portal/check_bys360_portal_experience_v3b3_social_import_center.py | sha256=60b158ea73500f86cf02dbde7af23ed86b2d96b40e7461c746014b4dcb32231a
- scripts/refactor/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_apply.py -> archive/scripts_retired_20260625_wave4/scripts/refactor/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_apply.py | sha256=70fb6c646a49591c9e6cfc7594cd8c95114a3d79dd4837d75ca8e9aadc7b4279

## Already Archived Files
- none

## Safety
- live_system_changed: False
- files_deleted: False
- files_moved_to_archive: True
- nginx_or_backup_created: False
- database_touched: False

## Decision
- V20A archive_wave4_safe listesindeki 15 guvenli tarihsel script arsivlendi.
- Dosyalar silinmedi; archive/scripts_retired_20260625_wave4 altina kaynak yol yapisi korunarak tasindi.
- Canli, Nginx, backup veya veritabani tarafina dokunulmadi.
- Risk markerli 68 dosya bu dalgaya dahil edilmedi.
