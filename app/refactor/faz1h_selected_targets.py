"""Faz 1H controlled family split spesifikasyonu."""

REQUIRED_SERVICE_MODULES = [
    "communication_phase1_service",
    "communication_phase2_service",
    "communication_phase3_service",
    "communication_phase4_service",
    "communication_phase5_service",
]

OPTIONAL_SERVICE_MODULES = [
    "communication_phase8_service",
    "communication_phase9_service",
    "communication_phase9a_service",
    "communication_phase9b_service",
    "communication_phase9c_service",
    "communication_phase9d_service",
]

REQUIRED_MODEL_MODULES = [
    "communication_phase1_models",
    "communication_phase2_models",
    "communication_phase3_models",
    "communication_phase4_models",
    "communication_phase5_models",
]

OPTIONAL_MODEL_MODULES: list[str] = []

SERVICE_REQUIRED_BRIDGE = "app.services.communication_required_service"
SERVICE_OPTIONAL_BRIDGE = "app.services.communication_optional_service"
MODEL_REQUIRED_BRIDGE = "app.models.communication_required_models"
MODEL_OPTIONAL_BRIDGE = "app.models.communication_optional_models"

FAMILY_SERVICE_BRIDGE_PATH = "app/services/communication_family_service.py"
FAMILY_MODEL_BRIDGE_PATH = "app/models/communication_family_models.py"

STAGE_ROOT = "refactor_staging/faz1h"
BACKUP_ROOT = "refactor_backups/faz1h"
REPORT_ROOT = "reports/faz1h"