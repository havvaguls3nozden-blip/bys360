# BYS360 Phase4J Ops Routes Residual V6 Analysis
- Generated at: 2026-06-25T14:01:06
- Target: app/admin/ops_routes.py
- Lines: 614
- Size: 23.1 KB
- Function count: 16
- Route function count: 15
- Helper function count: 1

## Largest remaining functions
- download_personnel_template | 68 lines | lines 405-472 | route=True
- personnel_profile | 53 lines | lines 524-576 | route=True
- performance_hierarchy_bulk_assign | 47 lines | lines 352-398 | route=True
- admin_users_bulk_delete | 38 lines | lines 223-260 | route=True
- admin_user_change_photo | 31 lines | lines 108-138 | route=True
- admin_user_archive | 24 lines | lines 167-190 | route=True
- admin_users_bulk_archive | 23 lines | lines 267-289 | route=True
- admin_user_delete | 20 lines | lines 197-216 | route=True
- admin_users_bulk_passive | 19 lines | lines 296-314 | route=True
- personnel_toggle_active | 18 lines | lines 479-496 | route=True
- admin_user_toggle_active | 16 lines | lines 145-160 | route=True
- personnel_delete | 15 lines | lines 503-517 | route=True
- admin_users_reset_all | 10 lines | lines 337-346 | route=True
- ensure_not_self_target | 3 lines | lines 611-613 | route=False
- admin_user_import | 2 lines | lines 321-322 | route=True
- admin_import_health_report | 2 lines | lines 329-330 | route=True

## Next candidates
- download_personnel_template
- personnel_profile
- performance_hierarchy_bulk_assign
- admin_users_bulk_delete
- admin_user_change_photo
- admin_user_archive
- admin_users_bulk_archive
- admin_user_delete
- admin_users_bulk_passive

## Recommendation
- ops_routes.py ana iki agir bloktan arindirildi.
- Kalan parcalar daha kucuk route wrapper/service bolmelerine uygundur.
- Bir sonraki guvenli hamle download_personnel_template veya personnel_profile govdesini service'e almak olabilir.
- Her bolme sonrasi compileall, import smoke ve architecture testleri calistirilmelidir.
