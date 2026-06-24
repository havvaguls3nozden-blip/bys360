"""Institutional live-core route package.

BYS360 Maintenance v13 P0 canlı kapısı kapsamında birim/pozisyon ve personel özlük
route aileleri paket importunda açıkça yüklenir. Kapsam dışı eğitim/strateji/
portal/repository route aileleri burada çağrılmaz.
"""
from __future__ import annotations


# BYS360_MAINTENANCE_V13_INSTITUTIONAL_CHILD_ROUTES_BEGIN
_LIVE_CHILD_ROUTE_MODULES = (
    "routes",
    "org_unit_routes",
    "hr_leave_attendance_routes",
    "hr_personnel_analytics_routes",
    "hr_personnel_delegation_routes",
    "hr_personnel_extension_routes",
    "hr_personnel_leave_routes",
    "hr_personnel_operations_routes",
    "hr_personnel_phase10_routes",
    "hr_personnel_phase11_routes",
    "hr_personnel_phase12_routes",
    "hr_personnel_phase13_routes",
    "hr_personnel_reports_routes",
    "hr_reports_routes",
    "hr_request_analytics_routes",
    "hr_request_task_routes",
    "hr_live_p0_shims",
)

for _module_name in _LIVE_CHILD_ROUTE_MODULES:
    __import__(f"{__name__}.{_module_name}", fromlist=["*"])

__all__ = ["_LIVE_CHILD_ROUTE_MODULES"]
# BYS360_MAINTENANCE_V13_INSTITUTIONAL_CHILD_ROUTES_END
