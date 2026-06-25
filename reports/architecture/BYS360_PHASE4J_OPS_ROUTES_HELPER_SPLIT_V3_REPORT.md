# BYS360 Phase4J Ops Routes Helper Split V3
- Generated at: 2026-06-25T13:38:39
- Target: app/admin/ops_routes.py
- Helper: app/admin/ops_helpers.py
- Before: 1220 lines, 51.1 KB
- After target: 1064 lines, 44.4 KB
- New helper: 234 lines, 10.2 KB

## Moved functions
- _profile_full_name
- _safe_text
- _resolve_user_by_sicil
- _build_org_path
- _serialize_manager_card
- _resolve_personnel_profile_hierarchy
- _canonicalize_import_headers
- _collapse_spaces
- _has_explicit_manager_columns
- get_default_first_login_password

## Safety
- Route decorator bulunan fonksiyonlar tasinmadi.
- Blueprint/route registration davranisi korunarak sadece helper fonksiyonlar tasindi.
- ops_routes.py helper fonksiyonlari yeni ops_helpers.py modulunden import ediyor.
