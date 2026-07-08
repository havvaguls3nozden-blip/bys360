from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions import db
from app.models.file_center_models import (  # noqa: F401
    FileAccessLog,
    FileAuditLog,
    FileCenterMailLog,
    FileCenterSetting,
    FileCenterRolePermission,
    FileDownloadLog,
    FileQuotaUsage,
    FileQuotaPolicy,
    FileUploadSession,
    FileUploadChunk,
    FileRequest,
    FileRequestUpload,
    FileSecurityScan,
    FileShareLink,
    FileStorageFolder,
    FileStorageItem,
    FileTransfer,
    FileTransferItem,
    FileTransferRecipient,
)

app = create_app()
with app.app_context():
    db.create_all()
    print("OK: BYS360 Dosya Merkezi local V1I tabloları hazırlandı.")
