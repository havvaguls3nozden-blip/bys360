"""Faz 1I required route bridge ve sembol envanteri spesifikasyonu."""

REQUIRED_ROUTE_MODULES = [
    "phase1_routes",
    "phase2_routes",
    "phase3_routes",
    "phase4_routes",
    "phase5_routes",
]

OPTIONAL_ROUTE_MODULES = [
    "phase8_routes",
    "phase9_routes",
    "phase9a_routes",
    "phase9b_routes",
    "phase9c_routes",
    "phase9d_routes",
]

REQUIRED_SERVICE_MODULES = [
    "communication_phase1_service",
    "communication_phase2_service",
    "communication_phase3_service",
    "communication_phase4_service",
    "communication_phase5_service",
]

REQUIRED_MODEL_MODULES = [
    "communication_phase1_models",
    "communication_phase2_models",
    "communication_phase3_models",
    "communication_phase4_models",
    "communication_phase5_models",
]

ROUTE_MANIFEST_PATH = "app/communication/route_manifest.py"
PHASE_FAMILY_ROUTES_PATH = "app/communication/phase_family_routes.py"
STAGE_ROOT = "refactor_staging/faz1i"
BACKUP_ROOT = "refactor_backups/faz1i"
REPORT_ROOT = "reports/faz1i"