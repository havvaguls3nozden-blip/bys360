
from app.core.datetime_utils import utc_now

from app.extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class SoftDeleteMixin:
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_archived = db.Column(db.Boolean, default=False, nullable=False, index=True)


class OwnershipMixin:
    created_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    updated_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )