# BYS360 Phase4J Admin User Action Routes Service Split V10B
- Generated at: 2026-06-25T14:32:55
- OK: True
- Target: app/admin/ops_routes.py
- Service: app/admin/ops_user_action_services.py
- Before target: 455 lines, 16.5 KB
- After target: 291 lines, 10.0 KB
- Service: 242 lines, 10.3 KB

## Route counts
- admin_users_bulk_delete: 1
- admin_user_change_photo: 1
- admin_user_archive: 1
- admin_users_bulk_archive: 1
- admin_user_delete: 1
- admin_users_bulk_passive: 1
- admin_user_toggle_active: 1
- admin_users_reset_all: 1

## Impl counts
- admin_users_bulk_delete_impl: 1
- admin_user_change_photo_impl: 1
- admin_user_archive_impl: 1
- admin_users_bulk_archive_impl: 1
- admin_user_delete_impl: 1
- admin_users_bulk_passive_impl: 1
- admin_user_toggle_active_impl: 1
- admin_users_reset_all_impl: 1

## Helper counts
- ensure_not_self_target: 1

## Self recursive calls
- admin_users_bulk_delete_impl: []
- admin_user_change_photo_impl: []
- admin_user_archive_impl: []
- admin_users_bulk_archive_impl: []
- admin_user_delete_impl: []
- admin_users_bulk_passive_impl: []
- admin_user_toggle_active_impl: []
- admin_users_reset_all_impl: []

## Safety
- Route decorator satirlari ops_routes.py icinde korundu.
- Route fonksiyon imzalari korunarak ince wrapper haline getirildi.
- Admin kullanici islem govdeleri ops_user_action_services.py icindeki implementation fonksiyonlarina tasindi.
- ensure_not_self_target helper'i circular import riskini onlemek icin servis dosyasina kopyalandi.
- Duplicate implementation ve self-recursive call kontrolleri yapildi.
