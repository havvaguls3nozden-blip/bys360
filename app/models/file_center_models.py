"""BYS360 Dosya Merkezi veri modelleri.

V1D kapsamı:
- Dosya metadata kaydı
- Güvenli misafir indirme bağlantısı
- Dosya isteği ve misafir yükleme bağlantısı
- Transfer, indirme, erişim, kota ve audit kayıtları

Dosyanın kendisi veritabanına yazılmaz; storage_path fiziksel dosya yolunu tutar.
"""
from __future__ import annotations

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models.base import TimestampMixin


class FileStorageFolder(TimestampMixin, db.Model):
    __tablename__ = "file_storage_folders"

    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("file_storage_folders.id"), nullable=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False, index=True)

    owner = db.relationship("User", foreign_keys=[owner_user_id])
    parent = db.relationship("FileStorageFolder", remote_side=[id])


class FileStorageItem(TimestampMixin, db.Model):
    __tablename__ = "file_storage_items"

    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    folder_id = db.Column(db.Integer, db.ForeignKey("file_storage_folders.id"), nullable=True, index=True)
    original_filename = db.Column(db.String(500), nullable=False)
    stored_filename = db.Column(db.String(500), nullable=False)
    storage_path = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.String(255), nullable=True)
    extension = db.Column(db.String(40), nullable=True, index=True)
    size_bytes = db.Column(db.BigInteger, nullable=False, default=0)
    sha256_hash = db.Column(db.String(64), nullable=False, index=True)
    status = db.Column(db.String(40), nullable=False, default="ready", index=True)
    scan_status = db.Column(db.String(40), nullable=False, default="pending", index=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    owner = db.relationship("User", foreign_keys=[owner_user_id])
    folder = db.relationship("FileStorageFolder", foreign_keys=[folder_id])

    @property
    def size_mb(self) -> float:
        return round((self.size_bytes or 0) / 1024 / 1024, 2)


class FileTransfer(TimestampMixin, db.Model):
    __tablename__ = "file_transfers"

    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(40), nullable=False, default="draft", index=True)
    expires_at = db.Column(db.DateTime, nullable=True, index=True)

    owner = db.relationship("User", foreign_keys=[owner_user_id])


class FileTransferItem(TimestampMixin, db.Model):
    __tablename__ = "file_transfer_items"

    id = db.Column(db.Integer, primary_key=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey("file_transfers.id"), nullable=False, index=True)
    file_id = db.Column(db.Integer, db.ForeignKey("file_storage_items.id"), nullable=False, index=True)

    transfer = db.relationship("FileTransfer", foreign_keys=[transfer_id])
    file = db.relationship("FileStorageItem", foreign_keys=[file_id])


class FileTransferRecipient(TimestampMixin, db.Model):
    __tablename__ = "file_transfer_recipients"

    id = db.Column(db.Integer, primary_key=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey("file_transfers.id"), nullable=False, index=True)
    recipient_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    recipient_email = db.Column(db.String(255), nullable=True, index=True)
    recipient_name = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(40), nullable=False, default="pending", index=True)

    transfer = db.relationship("FileTransfer", foreign_keys=[transfer_id])
    recipient_user = db.relationship("User", foreign_keys=[recipient_user_id])


class FileShareLink(TimestampMixin, db.Model):
    __tablename__ = "file_share_links"

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey("file_storage_items.id"), nullable=False, index=True)
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    public_token = db.Column(db.String(255), nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    max_downloads = db.Column(db.Integer, nullable=False, default=5)
    download_count = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    revoked_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    last_downloaded_at = db.Column(db.DateTime, nullable=True)

    file = db.relationship("FileStorageItem", foreign_keys=[file_id])
    created_by = db.relationship("User", foreign_keys=[created_by_user_id])

    def is_available(self) -> bool:
        now = utc_now()
        return bool(self.is_active and self.expires_at >= now and self.download_count < self.max_downloads)


class FileRequest(TimestampMixin, db.Model):
    __tablename__ = "file_requests"

    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    recipient_name = db.Column(db.String(255), nullable=True)
    recipient_email = db.Column(db.String(255), nullable=True, index=True)
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    public_token = db.Column(db.String(255), nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    max_file_gb = db.Column(db.Float, nullable=False, default=5)
    allowed_extensions = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(40), nullable=False, default="open", index=True)
    upload_count = db.Column(db.Integer, nullable=False, default=0)
    last_upload_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    revoked_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    owner = db.relationship("User", foreign_keys=[owner_user_id])

    def is_available(self) -> bool:
        now = utc_now()
        return bool(self.status == "open" and self.expires_at >= now)


class FileRequestUpload(TimestampMixin, db.Model):
    __tablename__ = "file_request_uploads"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("file_requests.id"), nullable=False, index=True)
    file_id = db.Column(db.Integer, db.ForeignKey("file_storage_items.id"), nullable=False, index=True)
    guest_name = db.Column(db.String(255), nullable=True)
    guest_email = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(80), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(40), nullable=False, default="uploaded", index=True)

    request = db.relationship("FileRequest", foreign_keys=[request_id])
    file = db.relationship("FileStorageItem", foreign_keys=[file_id])


class FileDownloadLog(TimestampMixin, db.Model):
    __tablename__ = "file_download_logs"

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey("file_storage_items.id"), nullable=False, index=True)
    share_link_id = db.Column(db.Integer, db.ForeignKey("file_share_links.id"), nullable=True, index=True)
    downloaded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    guest_label = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(80), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(40), nullable=False, default="success", index=True)

    file = db.relationship("FileStorageItem", foreign_keys=[file_id])
    share_link = db.relationship("FileShareLink", foreign_keys=[share_link_id])


class FileAccessLog(TimestampMixin, db.Model):
    __tablename__ = "file_access_logs"

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey("file_storage_items.id"), nullable=True, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(80), nullable=False, index=True)
    ip_address = db.Column(db.String(80), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    detail = db.Column(db.Text, nullable=True)


class FileQuotaUsage(TimestampMixin, db.Model):
    __tablename__ = "file_quota_usage"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True, index=True)
    used_bytes = db.Column(db.BigInteger, nullable=False, default=0)
    file_count = db.Column(db.Integer, nullable=False, default=0)

    user = db.relationship("User", foreign_keys=[user_id])


class FileSecurityScan(TimestampMixin, db.Model):
    __tablename__ = "file_security_scans"

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey("file_storage_items.id"), nullable=False, index=True)
    status = db.Column(db.String(40), nullable=False, default="pending", index=True)
    scanner = db.Column(db.String(120), nullable=True)
    result_message = db.Column(db.Text, nullable=True)
    scanned_at = db.Column(db.DateTime, nullable=True)

    file = db.relationship("FileStorageItem", foreign_keys=[file_id])


class FileAuditLog(TimestampMixin, db.Model):
    __tablename__ = "file_audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    file_id = db.Column(db.Integer, db.ForeignKey("file_storage_items.id"), nullable=True, index=True)
    action = db.Column(db.String(80), nullable=False, index=True)
    message = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(80), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)



class FileQuotaPolicy(TimestampMixin, db.Model):
    __tablename__ = "file_quota_policies"

    id = db.Column(db.Integer, primary_key=True)
    scope_type = db.Column(db.String(40), nullable=False, default="global", index=True)  # global, user, unit, role
    scope_value = db.Column(db.String(255), nullable=True, index=True)
    label = db.Column(db.String(255), nullable=False)
    max_storage_gb = db.Column(db.Float, nullable=False, default=25)
    max_single_file_gb = db.Column(db.Float, nullable=False, default=5)
    max_transfer_gb = db.Column(db.Float, nullable=False, default=20)
    warning_threshold_percent = db.Column(db.Integer, nullable=False, default=80)
    hard_stop_enabled = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    notes = db.Column(db.Text, nullable=True)

    created_by = db.relationship("User", foreign_keys=[created_by_user_id])


class FileUploadSession(TimestampMixin, db.Model):
    __tablename__ = "file_upload_sessions"

    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    session_token = db.Column(db.String(255), nullable=False, unique=True, index=True)
    original_filename = db.Column(db.String(500), nullable=False)
    total_size_bytes = db.Column(db.BigInteger, nullable=False, default=0)
    chunk_size_bytes = db.Column(db.Integer, nullable=False, default=10485760)
    total_chunks = db.Column(db.Integer, nullable=False, default=0)
    received_chunks = db.Column(db.Integer, nullable=False, default=0)
    received_bytes = db.Column(db.BigInteger, nullable=False, default=0)
    sha256_hash = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(40), nullable=False, default="prepared", index=True)
    temp_dir = db.Column(db.Text, nullable=True)
    finalized_file_id = db.Column(db.Integer, db.ForeignKey("file_storage_items.id"), nullable=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=True, index=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)

    owner = db.relationship("User", foreign_keys=[owner_user_id])
    finalized_file = db.relationship("FileStorageItem", foreign_keys=[finalized_file_id])


class FileUploadChunk(TimestampMixin, db.Model):
    __tablename__ = "file_upload_chunks"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("file_upload_sessions.id"), nullable=False, index=True)
    chunk_index = db.Column(db.Integer, nullable=False, index=True)
    size_bytes = db.Column(db.Integer, nullable=False, default=0)
    sha256_hash = db.Column(db.String(64), nullable=True)
    storage_path = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(40), nullable=False, default="prepared", index=True)

    session = db.relationship("FileUploadSession", foreign_keys=[session_id])


class FileCenterMailLog(TimestampMixin, db.Model):
    __tablename__ = "file_center_mail_logs"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("file_requests.id"), nullable=True, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    recipient_email = db.Column(db.String(255), nullable=False, index=True)
    subject = db.Column(db.String(500), nullable=False)
    body = db.Column(db.Text, nullable=True)
    purpose = db.Column(db.String(80), nullable=False, default="request_invitation", index=True)
    status = db.Column(db.String(40), nullable=False, default="pending", index=True)
    error_message = db.Column(db.Text, nullable=True)
    smtp_host = db.Column(db.String(255), nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)

    request = db.relationship("FileRequest", foreign_keys=[request_id])
    actor = db.relationship("User", foreign_keys=[actor_user_id])


class FileCenterRolePermission(TimestampMixin, db.Model):
    __tablename__ = "file_center_role_permissions"

    id = db.Column(db.Integer, primary_key=True)
    role_key = db.Column(db.String(120), nullable=False, unique=True, index=True)
    role_label = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    can_use = db.Column(db.Boolean, nullable=False, default=True)
    can_upload_files = db.Column(db.Boolean, nullable=False, default=True)
    can_download_files = db.Column(db.Boolean, nullable=False, default=True)
    can_create_guest_links = db.Column(db.Boolean, nullable=False, default=True)
    can_create_guest_upload_requests = db.Column(db.Boolean, nullable=False, default=True)
    can_view_transfers = db.Column(db.Boolean, nullable=False, default=True)
    can_view_requests = db.Column(db.Boolean, nullable=False, default=True)
    can_use_chunk_upload = db.Column(db.Boolean, nullable=False, default=True)
    can_view_logs = db.Column(db.Boolean, nullable=False, default=False)
    can_manage_security = db.Column(db.Boolean, nullable=False, default=False)
    can_manage_admin = db.Column(db.Boolean, nullable=False, default=False)
    can_manage_maintenance = db.Column(db.Boolean, nullable=False, default=False)
    can_manage_settings = db.Column(db.Boolean, nullable=False, default=False)
    can_manage_quota_policy = db.Column(db.Boolean, nullable=False, default=False)
    can_manage_role_matrix = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    updated_by = db.relationship("User", foreign_keys=[updated_by_user_id])


class FileCenterSetting(TimestampMixin, db.Model):
    __tablename__ = "file_center_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), nullable=False, unique=True, index=True)
    value = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(40), nullable=False, default="string")
    group_key = db.Column(db.String(80), nullable=False, default="general", index=True)
    label = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    updated_by = db.relationship("User", foreign_keys=[updated_by_user_id])
