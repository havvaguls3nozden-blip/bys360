"""Dijital Arşiv SQLAlchemy model taslakları.

DA-2B:
- Yalnızca digital_archive_* tablo ailesini tanımlar.
- Migration üretmez.
- Mevcut BYS360 tablolarında değişiklik yapmaz.
"""

from datetime import datetime

from app import db


class DigitalArchiveCategory(db.Model):
    """Dosya planı ve arşiv kategori ağacı."""

    __tablename__ = "digital_archive_categories"

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("digital_archive_categories.id"), nullable=True)
    code = db.Column(db.String(80), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    parent = db.relationship("DigitalArchiveCategory", remote_side=[id], backref="children")


class DigitalArchiveRetentionPolicy(db.Model):
    """Saklama süresi, kalıcı arşiv ve imha politika tanımı."""

    __tablename__ = "digital_archive_retention_policies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    retention_years = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(80), nullable=False, default="review")
    requires_approval = db.Column(db.Boolean, nullable=False, default=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class DigitalArchivePhysicalLocation(db.Model):
    """Fiziksel arşiv konumu ve belge hareket bilgisi."""

    __tablename__ = "digital_archive_physical_locations"

    id = db.Column(db.Integer, primary_key=True)
    archive_room = db.Column(db.String(120), nullable=True)
    cabinet_no = db.Column(db.String(80), nullable=True)
    shelf_no = db.Column(db.String(80), nullable=True)
    box_no = db.Column(db.String(80), nullable=True)
    folder_no = db.Column(db.String(80), nullable=True)
    file_no = db.Column(db.String(80), nullable=True)
    physical_status = db.Column(db.String(80), nullable=False, default="original")
    delivered_to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    returned_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class DigitalArchiveDocument(db.Model):
    """Belge kayıt kartı."""

    __tablename__ = "digital_archive_documents"

    id = db.Column(db.Integer, primary_key=True)
    document_no = db.Column(db.String(120), nullable=False, unique=True, index=True)
    title = db.Column(db.String(500), nullable=False)
    document_type = db.Column(db.String(120), nullable=False)
    document_date = db.Column(db.Date, nullable=True)
    subject = db.Column(db.Text, nullable=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("digital_archive_categories.id"),
        nullable=False,
    )
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    organization_unit_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_units.id"),
        nullable=True,
    )
    related_personnel_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    confidentiality_level = db.Column(db.String(80), nullable=False, default="internal")
    status = db.Column(db.String(80), nullable=False, default="draft")
    retention_policy_id = db.Column(
        db.Integer,
        db.ForeignKey("digital_archive_retention_policies.id"),
        nullable=True,
    )
    physical_location_id = db.Column(
        db.Integer,
        db.ForeignKey("digital_archive_physical_locations.id"),
        nullable=True,
    )
    tags = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    category = db.relationship("DigitalArchiveCategory", backref="documents")
    retention_policy = db.relationship("DigitalArchiveRetentionPolicy", backref="documents")
    physical_location = db.relationship("DigitalArchivePhysicalLocation", backref="documents")


class DigitalArchiveDocumentVersion(db.Model):
    """Belge dosyası ve versiyon geçmişi."""

    __tablename__ = "digital_archive_document_versions"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(
        db.Integer,
        db.ForeignKey("digital_archive_documents.id"),
        nullable=False,
        index=True,
    )
    version_no = db.Column(db.Integer, nullable=False, default=1)
    file_name = db.Column(db.String(500), nullable=False)
    storage_path = db.Column(db.String(1000), nullable=False)
    mime_type = db.Column(db.String(180), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    sha256_hash = db.Column(db.String(128), nullable=True, index=True)
    revision_note = db.Column(db.Text, nullable=True)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    document = db.relationship("DigitalArchiveDocument", backref="versions")


class DigitalArchiveAccessRule(db.Model):
    """Belge bazlı erişim kuralı."""

    __tablename__ = "digital_archive_access_rules"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(
        db.Integer,
        db.ForeignKey("digital_archive_documents.id"),
        nullable=False,
        index=True,
    )
    role_name = db.Column(db.String(120), nullable=True)
    organization_unit_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_units.id"),
        nullable=True,
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    can_view = db.Column(db.Boolean, nullable=False, default=True)
    can_download = db.Column(db.Boolean, nullable=False, default=False)
    can_update = db.Column(db.Boolean, nullable=False, default=False)
    can_delete = db.Column(db.Boolean, nullable=False, default=False)
    can_manage_access = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    document = db.relationship("DigitalArchiveDocument", backref="access_rules")


class DigitalArchiveAuditEvent(db.Model):
    """Belge hareketleri için modül içi denetim izi."""

    __tablename__ = "digital_archive_audit_events"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(
        db.Integer,
        db.ForeignKey("digital_archive_documents.id"),
        nullable=True,
        index=True,
    )
    event_type = db.Column(db.String(120), nullable=False, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    ip_address = db.Column(db.String(80), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    details_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    document = db.relationship("DigitalArchiveDocument", backref="audit_events")


class DigitalArchiveEntityLink(db.Model):
    """Belgenin BYS360 içindeki diğer süreçlerle ilişkisi."""

    __tablename__ = "digital_archive_entity_links"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(
        db.Integer,
        db.ForeignKey("digital_archive_documents.id"),
        nullable=False,
        index=True,
    )
    entity_type = db.Column(db.String(120), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    relation_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    document = db.relationship("DigitalArchiveDocument", backref="entity_links")


class DigitalArchiveOcrJob(db.Model):
    """OCR kuyruğu ve çıkarılan metin alanı."""

    __tablename__ = "digital_archive_ocr_jobs"

    id = db.Column(db.Integer, primary_key=True)
    document_version_id = db.Column(
        db.Integer,
        db.ForeignKey("digital_archive_document_versions.id"),
        nullable=False,
        index=True,
    )
    status = db.Column(db.String(80), nullable=False, default="pending")
    extracted_text = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    document_version = db.relationship("DigitalArchiveDocumentVersion", backref="ocr_jobs")
