"""Model altyapisi ve ortak mixinler."""

from datetime import datetime

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