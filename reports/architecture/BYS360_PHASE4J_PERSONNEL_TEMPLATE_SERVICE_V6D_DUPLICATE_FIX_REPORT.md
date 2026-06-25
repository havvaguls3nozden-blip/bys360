# BYS360 Phase4J Personnel Template Service V6D Duplicate Fix Report
- Generated at: 2026-06-25T14:11:42
- OK: True
- Service impl count before: 2
- Service impl count after: 1
- Route wrapper count after: 1
- ops_routes.py lines: 549
- ops_personnel_services.py lines: 115
- Self recursive call lines: []

## Removed duplicate ranges
- lines 117-118 | 2 lines

## Checks
- service_impl_count_is_one: True
- route_wrapper_count_is_one: True
- service_impl_not_self_recursive: True
- import_ops_routes: True
- import_ops_personnel_services: True
- has_route_wrapper: True
- has_service_impl: True
- create_app: True

- Route count: 941
