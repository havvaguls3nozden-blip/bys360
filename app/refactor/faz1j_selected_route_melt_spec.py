"""Faz 1J secili route govde eritme spesifikasyonu."""

TARGETS = [
    {
        "source_module": "phase4_routes",
        "target_module": "reporting_routes",
        "target_relpath": "app/communication/reporting_routes.py",
        "family": "reporting",
        "phase_label": "faz4",
    },
    {
        "source_module": "phase5_routes",
        "target_module": "operations_routes",
        "target_relpath": "app/communication/operations_routes.py",
        "family": "operations",
        "phase_label": "faz5",
    },
]

ROUTE_MANIFEST_PATH = "app/communication/route_manifest.py"
PHASE_FAMILY_ROUTES_PATH = "app/communication/phase_family_routes.py"
COMMUNICATION_ROUTES_HUB_PATH = "app/communication/routes.py"
BACKUP_ROOT = "refactor_backups/faz1j"
STAGE_ROOT = "refactor_staging/faz1j"
REPORT_ROOT = "reports/faz1j"