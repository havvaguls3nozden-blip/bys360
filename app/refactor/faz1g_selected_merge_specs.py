"""Faz 1G secili dusuk riskli birlesme spesifikasyonu.

Bu faz communication ailesinde uc dusuk riskli hareket yapar:
1) route manifest icindeki phase route importlarini tek bridge module toplar
2) canonical non-phase dosyalardaki direct phase importlarini family bridge'e yonlendirir
3) yedek/receipt/verify ciktisi uretir
"""

ROUTE_BRIDGE_MODULE = "phase_family_routes"

REQUIRED_PHASE_ROUTES = [
    "phase1_routes",
    "phase2_routes",
    "phase3_routes",
    "phase4_routes",
    "phase5_routes",
]

OPTIONAL_PHASE_ROUTES = [
    "phase8_routes",
    "phase9_routes",
    "phase9a_routes",
    "phase9b_routes",
    "phase9c_routes",
    "phase9d_routes",
]

SERVICE_BRIDGE_IMPORT_PREFIX = "app.services.communication_family_service"
MODEL_BRIDGE_IMPORT_PREFIX = "app.models.communication_family_models"

SERVICE_PHASE_PREFIX = "app.services.communication_phase"
MODEL_PHASE_PREFIX = "app.models.communication_phase"

# Sadece canonical / non-phase dosyalarda rewrite yap.
PATCH_ROOTS = [
    "app/communication",
    "app/services",
    "app/models",
    "app/routes",
]

SKIP_BASENAME_PREFIXES = (
    "phase",
    "communication_phase",
)

SKIP_PATH_PARTS = {
    "__pycache__",
    "refactor_backups",
    "refactor_quarantine",
    "refactor_staging",
}