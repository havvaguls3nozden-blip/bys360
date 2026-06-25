# BYS360 Phase4J Admin User Action Routes V10 Analysis
- Generated at: 2026-06-25T14:27:42
- Target: app/admin/ops_routes.py
- Target lines: 455
- Found count: 8
- Total candidate lines: 181

## Missing
- none

## Unsafe internal refs
- admin_user_archive: ensure_not_self_target
- admin_user_toggle_active: ensure_not_self_target

## Functions
- `admin_users_bulk_delete` | 38 lines | lines 226-263 | route=True | returns=2
  - calls: commit, flash, get, getattr, getlist, menu_key_required, normalize_int_list, redirect, rollback, route, safe_delete_user_by_id, url_for
- `admin_user_change_photo` | 31 lines | lines 111-141 | route=True | returns=5
  - calls: _delete_profile_photo_file, _save_profile_photo, commit, flash, get, getattr, lower, menu_key_required, redirect, rollback, route, strip, url_for, utc_now
- `admin_user_archive` | 24 lines | lines 170-193 | route=True | returns=3
  - internal refs: ensure_not_self_target
  - calls: bool, commit, ensure_not_self_target, flash, get, getattr, hasattr, menu_key_required, redirect, rollback, route, str, url_for, utc_now
- `admin_users_bulk_archive` | 23 lines | lines 270-292 | route=True | returns=2
  - calls: bool, commit, flash, get, getattr, getlist, hasattr, menu_key_required, normalize_int_list, redirect, route, url_for, utc_now
- `admin_user_delete` | 20 lines | lines 200-219 | route=True | returns=3
  - calls: commit, flash, get, getattr, menu_key_required, redirect, rollback, route, safe_delete_user_by_id, url_for
- `admin_users_bulk_passive` | 19 lines | lines 299-317 | route=True | returns=2
  - calls: bool, commit, flash, get, getattr, getlist, menu_key_required, normalize_int_list, redirect, route, url_for
- `admin_user_toggle_active` | 16 lines | lines 148-163 | route=True | returns=2
  - internal refs: ensure_not_self_target
  - calls: commit, ensure_boolean_toggle, ensure_not_self_target, flash, get, getattr, menu_key_required, redirect, rollback, route, str, url_for
- `admin_users_reset_all` | 10 lines | lines 340-349 | route=True | returns=1
  - calls: commit, flash, menu_key_required, redirect, reset_all_personnel_and_related_data, rollback, route, url_for

## Recommendation
- Bu grup admin kullanici islem route'larini kapsar.
- unsafe_internal_refs bos ise fonksiyonlar ops_user_action_services.py icine grup halinde tasinabilir.
- Toplu tasima ops_routes.py dosyasini anlamli sekilde kuculturken route decorator satirlarini korumali.
- Tasima sonrasi compileall, import smoke, duplicate kontrol ve architecture testleri calistirilmelidir.
