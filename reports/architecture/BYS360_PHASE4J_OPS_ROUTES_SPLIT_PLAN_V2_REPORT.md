# BYS360 Phase4J Ops Routes Split Plan V2
- Generated at: 2026-06-25T13:34:18
- Target: app/admin/ops_routes.py
- Size: 51.1 KB
- Total lines: 1220
- Function count: 26
- Route function count: 15

## Largest functions
- admin_user_import | lines 466-746 | 281 lines
- admin_import_health_report | lines 753-927 | 175 lines
- _resolve_personnel_profile_hierarchy | lines 96-163 | 68 lines
- download_personnel_template | lines 1002-1069 | 68 lines
- personnel_profile | lines 1121-1173 | 53 lines
- performance_hierarchy_bulk_assign | lines 949-995 | 47 lines
- admin_users_bulk_delete | lines 368-405 | 38 lines
- admin_user_change_photo | lines 253-283 | 31 lines
- _has_explicit_manager_columns | lines 218-246 | 29 lines
- admin_user_archive | lines 312-335 | 24 lines
- admin_users_bulk_archive | lines 412-434 | 23 lines
- admin_user_delete | lines 342-361 | 20 lines
- admin_users_bulk_passive | lines 441-459 | 19 lines
- personnel_toggle_active | lines 1076-1093 | 18 lines
- admin_user_toggle_active | lines 290-305 | 16 lines
- personnel_delete | lines 1100-1114 | 15 lines
- _serialize_manager_card | lines 81-93 | 13 lines
- _build_org_path | lines 67-78 | 12 lines
- _canonicalize_import_headers | lines 200-210 | 11 lines
- admin_users_reset_all | lines 934-943 | 10 lines
- get_default_first_login_password | lines 1213-1220 | 8 lines
- _profile_full_name | lines 46-52 | 7 lines
- _resolve_user_by_sicil | lines 60-64 | 5 lines
- _safe_text | lines 55-57 | 3 lines
- _collapse_spaces | lines 213-215 | 3 lines

## Suggested route groups

### audit_logs
- no route detected

### system_health
- admin_import_health_report

### backup_release
- no route detected

### jobs_scheduler
- no route detected

### security_ops
- no route detected

### misc
- admin_user_change_photo
- admin_user_toggle_active
- admin_user_archive
- admin_user_delete
- admin_users_bulk_delete
- admin_users_bulk_archive
- admin_users_bulk_passive
- admin_user_import
- admin_users_reset_all
- performance_hierarchy_bulk_assign
- download_personnel_template
- personnel_toggle_active
- personnel_delete
- personnel_profile

## Safe split strategy
- Once yeni app/admin/ops/ yardimci paket klasoru olusturulacak.
- Blueprint veya route registration davranisi degistirilmeyecek.
- Ilk turda sadece saf yardimci fonksiyonlar veya rapor/hesaplama bloklari tasinacak.
- Route decorator bulunan fonksiyonlar ikinci turda grup bazli tasinacak.
- Her tasima sonrasi compileall ve route-map smoke calistirilacak.
