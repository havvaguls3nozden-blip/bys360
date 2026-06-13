from app.extensions import db
from app.model_mixins import OwnershipMixin, SoftDeleteMixin, TimestampMixin


class PublicationIssue(TimestampMixin, SoftDeleteMixin, OwnershipMixin, db.Model):
    __tablename__ = "publication_issues"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    subtitle = db.Column(db.String(255), nullable=True)
    summary = db.Column(db.Text, nullable=True)

    publication_type = db.Column(db.String(40), nullable=False, default="bulletin", index=True)
    issue_no = db.Column(db.String(50), nullable=True, index=True)
    publication_period = db.Column(db.String(100), nullable=True, index=True)
    publication_date = db.Column(db.Date, nullable=True, index=True)

    status = db.Column(db.String(30), nullable=False, default="published", index=True)
    is_featured = db.Column(db.Boolean, nullable=False, default=False, index=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0, index=True)

    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True, index=True)
    storage_path = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(150), nullable=True)
    file_size = db.Column(db.BigInteger, nullable=False, default=0)
    page_count = db.Column(db.Integer, nullable=True)
    cover_image_path = db.Column(db.String(500), nullable=True)

    allow_download = db.Column(db.Boolean, nullable=False, default=True)
    visibility_level = db.Column(db.String(30), nullable=False, default="institution", index=True)