from __future__ import annotations

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models.base import TimestampMixin


class CommunicationBulletin(TimestampMixin, db.Model):
    __tablename__ = "communication_bulletins"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    summary = db.Column(db.String(500), nullable=True)
    content = db.Column(db.Text, nullable=False)

    bulletin_type = db.Column(db.String(50), nullable=False, default="duyuru", index=True)
    priority = db.Column(db.String(20), nullable=False, default="normal", index=True)
    status = db.Column(db.String(30), nullable=False, default="draft", index=True)

    is_pinned = db.Column(db.Boolean, nullable=False, default=False, index=True)
    require_ack = db.Column(db.Boolean, nullable=False, default=False)

    publish_at = db.Column(db.DateTime, nullable=True, index=True)
    expire_at = db.Column(db.DateTime, nullable=True, index=True)

    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    published_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    created_by = db.relationship("User", foreign_keys=[created_by_user_id])
    published_by = db.relationship("User", foreign_keys=[published_by_user_id])

    audiences = db.relationship(
        "CommunicationBulletinAudience",
        back_populates="bulletin",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    receipts = db.relationship(
        "CommunicationBulletinReceipt",
        back_populates="bulletin",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CommunicationBulletin {self.id} {self.title}>"


class CommunicationBulletinAudience(TimestampMixin, db.Model):
    __tablename__ = "communication_bulletin_audiences"

    id = db.Column(db.Integer, primary_key=True)
    bulletin_id = db.Column(
        db.Integer,
        db.ForeignKey("communication_bulletins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_type = db.Column(db.String(30), nullable=False, index=True)  # all / role / unit / user
    target_value = db.Column(db.String(255), nullable=True, index=True)

    bulletin = db.relationship("CommunicationBulletin", back_populates="audiences")

    __table_args__ = (
        db.Index("ix_comm_bulletin_audience_type_value", "target_type", "target_value"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CommunicationBulletinAudience B{self.bulletin_id} {self.target_type}:{self.target_value}>"


class CommunicationBulletinReceipt(TimestampMixin, db.Model):
    __tablename__ = "communication_bulletin_receipts"

    id = db.Column(db.Integer, primary_key=True)
    bulletin_id = db.Column(
        db.Integer,
        db.ForeignKey("communication_bulletins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    delivered_at = db.Column(db.DateTime, nullable=True, default=utc_now)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    is_acknowledged = db.Column(db.Boolean, nullable=False, default=False, index=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)

    bulletin = db.relationship("CommunicationBulletin", back_populates="receipts")
    user = db.relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        db.UniqueConstraint("bulletin_id", "user_id", name="uq_comm_bulletin_receipt_user"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CommunicationBulletinReceipt B{self.bulletin_id} U{self.user_id}>"