# BYS360 Phase4J Personnel Profile V7 Analysis
- Generated at: 2026-06-25T14:13:14
- Function: personnel_profile
- Lines: 459-511 (53 lines)

## Decorators
- `main_bp.route('/personnel/<int:user_id>/profile')`
- `login_required`
- `admin_required`
- `menu_key_required('admin_users')`

## External refs
- User
- _profile_full_name
- _resolve_personnel_profile_hierarchy
- admin_required
- build_personnel_profile_chain_ai_panel
- db
- flash
- login_required
- main_bp
- menu_key_required
- redirect
- safe_render
- url_for

## Missing in service
- none

## Call names
- _profile_full_name
- _resolve_personnel_profile_hierarchy
- bool
- build_personnel_profile_chain_ai_panel
- build_personnel_profile_hr_context
- flash
- get
- getattr
- hasattr
- menu_key_required
- redirect
- route
- safe_render
- strip
- url_for

## Recommendation
- personnel_profile route fonksiyonu wrapper/service yontemiyle ops_personnel_services.py icine alinabilir.
- Split yapmadan once missing_in_service listesindeki isimler servis dosyasinda garanti altina alinmalidir.
- Tasima sonrasi duplicate kontrol, compileall, import smoke ve architecture testleri calistirilmelidir.
