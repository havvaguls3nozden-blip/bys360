from __future__ import annotations

ROUTE_FAMILY = "admin"

REQUIRED_ROUTE_MODULES = [
    "routes",
    "ops_routes",
    "go_live_routes",
    "ai_routes",
    "ai_phase2_routes",
    "ai_phase5_routes",
    "ai_phase6_routes",
    "ai_phase7_routes",
    "ai_phase8_routes",
    "ai_phase9_routes",
    "ai_phase10_routes",
    "ai_phase11_routes",
    "ai_phase12_routes",
]

OPTIONAL_ROUTE_MODULES: list[str] = [
    "role_matrix_routes",
]

ROUTE_BUCKETS = {
    "core_admin": ["routes", "ops_routes", "go_live_routes"],
    "ai_admin": [name for name in REQUIRED_ROUTE_MODULES if name.startswith("ai_") or name == "ai_routes"],
}
