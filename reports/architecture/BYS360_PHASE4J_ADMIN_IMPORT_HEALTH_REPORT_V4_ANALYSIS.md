# BYS360 Phase4J Admin Import Health Report V4 Analysis
- Generated at: 2026-06-25T13:42:16
- Function: admin_import_health_report
- Lines: 606-780 (175 lines)

## Decorators
- `main_bp.route('/admin/import-health-report')`
- `login_required`
- `admin_required`
- `menu_key_required('admin_users')`

## External refs
- OrganizationUnit
- User
- admin_required
- build_import_health_priority_ai_panel
- build_import_health_simulation_ai_panel
- flash
- login_required
- main_bp
- menu_key_required
- request
- safe_render

## Call names
- all
- any
- append
- asc
- build_import_health_priority_ai_panel
- build_import_health_simulation_ai_panel
- filter
- flash
- get
- int
- is_
- items
- join
- len
- lower
- menu_key_required
- order_by
- route
- safe_render
- setdefault
- sort
- str
- strip
- sum

## Suggestion
- Bu fonksiyon route decorator tasidigi icin ilk hamlede davranis korunarak wrapper yontemi kullanilmali.
- Yeni app/admin/ops_health_routes.py icinde ayni fonksiyon tasinmadan once import bagimliliklari netlestirilmeli.
- Guvenli alternatif: ops_routes.py icindeki route fonksiyonu ince wrapper olarak kalsin, agir hesaplama helper/service fonksiyonuna tasinsin.
