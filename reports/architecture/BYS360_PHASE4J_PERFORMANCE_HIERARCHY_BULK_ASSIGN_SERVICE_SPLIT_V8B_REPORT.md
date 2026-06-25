# BYS360 Phase4J Performance Hierarchy Bulk Assign Service Split V8B
- Generated at: 2026-06-25T14:22:35
- OK: True
- Target: app/admin/ops_routes.py
- Service: app/admin/ops_performance_services.py
- Route function: performance_hierarchy_bulk_assign
- Service function: performance_hierarchy_bulk_assign_impl
- Route wrapper count: 1
- Service impl count: 1
- Self recursive call lines: []
- Before target: 499 lines, 18.7 KB
- After target: 455 lines, 16.5 KB
- Service: 96 lines, 5.0 KB

## Safety
- Route decorator satirlari ops_routes.py icinde korundu.
- Route fonksiyon imzasi korunarak ince wrapper haline getirildi.
- Agir performance_hierarchy_bulk_assign govdesi ops_performance_services.py icindeki implementation fonksiyonuna tasindi.
- Duplicate implementation ve self-recursive call kontrolleri yapildi.
