from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app

app = create_app()
with app.app_context():
    endpoints = {rule.endpoint: rule.rule for rule in app.url_map.iter_rules()}
    required = [
        "main.file_center_home",
        "main.file_center_upload",
        "main.file_center_download",
        "main.file_center_create_guest_link",
        "main.file_center_guest_download",
        "main.file_center_settings",
        "main.file_center_role_matrix",
        "main.file_center_role_matrix_save",
        "main.file_center_requests",
        "main.file_center_guest_upload",
        "main.file_center_admin_dashboard",
        "main.file_center_maintenance",
        "main.file_center_security",
        "main.file_center_security_scan_pending",
        "main.file_center_security_scan_file",
        "main.file_center_security_quarantine_file",
        "main.file_center_security_release_file",
        "main.file_center_security_block_file",
        "main.file_center_quota",
        "main.file_center_quota_policy_save",
        "main.file_center_quota_policy_deactivate",
        "main.file_center_chunk_upload",
        "main.file_center_chunk_upload_session_create",
        "main.file_center_chunk_upload_session_cancel",
    ]
    missing = [x for x in required if x not in endpoints]
    if missing:
        raise SystemExit("Eksik route: " + ", ".join(missing))
    print("OK: Dosya Merkezi V1K route kayıtları hazır.")
    for key in required:
        print(f"{key} -> {endpoints[key]}")
