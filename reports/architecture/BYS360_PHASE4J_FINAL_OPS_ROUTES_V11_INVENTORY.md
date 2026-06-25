# BYS360 Phase4J Final Ops Routes V11 Inventory
- Generated at: 2026-06-25T14:37:39
- Target: app/admin/ops_routes.py
- Lines: 291
- Size: 10.0 KB
- Function count: 16
- Route function count: 15
- Helper function count: 1

## Largest remaining routes
- personnel_toggle_active | 18 lines | lines 207-224
- personnel_delete | 15 lines | lines 231-245
- admin_user_change_photo | 2 lines | lines 112-113
- admin_user_toggle_active | 2 lines | lines 120-121
- admin_user_archive | 2 lines | lines 128-129
- admin_user_delete | 2 lines | lines 136-137
- admin_users_bulk_delete | 2 lines | lines 144-145
- admin_users_bulk_archive | 2 lines | lines 152-153
- admin_users_bulk_passive | 2 lines | lines 160-161
- admin_user_import | 2 lines | lines 168-169
- admin_import_health_report | 2 lines | lines 176-177
- admin_users_reset_all | 2 lines | lines 184-185
- performance_hierarchy_bulk_assign | 2 lines | lines 191-192
- download_personnel_template | 2 lines | lines 199-200
- personnel_profile | 2 lines | lines 252-253

## Largest remaining functions
- personnel_toggle_active | 18 lines | lines 207-224 | route=True
- personnel_delete | 15 lines | lines 231-245 | route=True
- ensure_not_self_target | 3 lines | lines 288-290 | route=False
- admin_user_change_photo | 2 lines | lines 112-113 | route=True
- admin_user_toggle_active | 2 lines | lines 120-121 | route=True
- admin_user_archive | 2 lines | lines 128-129 | route=True
- admin_user_delete | 2 lines | lines 136-137 | route=True
- admin_users_bulk_delete | 2 lines | lines 144-145 | route=True
- admin_users_bulk_archive | 2 lines | lines 152-153 | route=True
- admin_users_bulk_passive | 2 lines | lines 160-161 | route=True
- admin_user_import | 2 lines | lines 168-169 | route=True
- admin_import_health_report | 2 lines | lines 176-177 | route=True
- admin_users_reset_all | 2 lines | lines 184-185 | route=True
- performance_hierarchy_bulk_assign | 2 lines | lines 191-192 | route=True
- download_personnel_template | 2 lines | lines 199-200 | route=True
- personnel_profile | 2 lines | lines 252-253 | route=True

## Completion note
- ops_routes.py 1220 satirdan 291 satir seviyesine indirildi.
- Agir route govdeleri helper/service dosyalarina ayrildi.
- Kalan route fonksiyonlari buyuk olasilikla ince wrapper veya kucuk operasyon fonksiyonlaridir.
