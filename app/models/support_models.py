"""Destek ve Talep Yönetimi veri modelleri."""
from __future__ import annotations


from datetime import datetime

from app.core.datetime_utils import utc_now

from app.extensions import db
from .base import TimestampMixin


class SupportCategory(TimestampMixin, db.Model):
    __tablename__ = "support_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    tickets = db.relationship("SupportTicket", back_populates="category", lazy="dynamic")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SupportCategory {self.name}>"


class SupportTicket(TimestampMixin, db.Model):
    __tablename__ = "support_tickets"

    id = db.Column(db.Integer, primary_key=True)
    ticket_no = db.Column(db.String(40), nullable=False, unique=True, index=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    ticket_type = db.Column(db.String(50), nullable=False, index=True)
    module_name = db.Column(db.String(120), nullable=False, index=True)
    page_url = db.Column(db.String(255), nullable=True)
    priority = db.Column(db.String(20), nullable=False, default="normal", index=True)
    status = db.Column(db.String(30), nullable=False, default="open", index=True)

    category_id = db.Column(db.Integer, db.ForeignKey("support_categories.id"), nullable=True, index=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    organization_unit_id = db.Column(db.Integer, db.ForeignKey("organization_units.id"), nullable=True, index=True)

    sicil_no_snapshot = db.Column(db.String(50), nullable=True, index=True)
    full_name_snapshot = db.Column(db.String(255), nullable=True)
    unit_name_snapshot = db.Column(db.String(255), nullable=True)
    is_private = db.Column(db.Boolean, nullable=False, default=False)
    closed_at = db.Column(db.DateTime, nullable=True)

    category = db.relationship("SupportCategory", back_populates="tickets")
    created_by = db.relationship("User", foreign_keys=[created_by_user_id])
    assigned_to = db.relationship("User", foreign_keys=[assigned_to_user_id])
    organization_unit = db.relationship("OrganizationUnit", foreign_keys=[organization_unit_id])

    messages = db.relationship(
        "SupportTicketMessage",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="SupportTicketMessage.created_at.asc()",
    )
    attachments = db.relationship(
        "SupportTicketAttachment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="SupportTicketAttachment.created_at.desc()",
    )
    status_history = db.relationship(
        "SupportTicketStatusHistory",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="SupportTicketStatusHistory.created_at.desc()",
    )
    feedback_ratings = db.relationship(
        "SupportFeedbackRating",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="SupportFeedbackRating.created_at.desc()",
    )

    @property
    def status_label(self) -> str:
        labels = {
            "open": "Açıldı",
            "reviewing": "İnceleniyor",
            "waiting_info": "Bilgi Bekleniyor",
            "assigned": "Atandı",
            "planned": "Geliştirme Planına Alındı",
            "resolved": "Çözüldü",
            "closed": "Kapatıldı",
            "rejected": "Reddedildi",
        }
        return labels.get((self.status or "").strip().lower(), self.status or "-")

    @property
    def priority_label(self) -> str:
        labels = {
            "low": "Düşük",
            "normal": "Normal",
            "high": "Yüksek",
            "critical": "Kritik",
        }
        return labels.get((self.priority or "").strip().lower(), self.priority or "-")

    @property
    def latest_status_entry(self):
        return self.status_history[0] if self.status_history else None

    @property
    def status_date(self):
        latest = self.latest_status_entry
        return getattr(latest, "created_at", None) or self.updated_at or self.created_at

    @property
    def sub_status_text(self) -> str:
        latest = self.latest_status_entry
        note = (getattr(latest, "note", None) or "").strip()
        return note or "-"

    @property
    def resolution_text(self) -> str:
        closing_statuses = {"resolved", "closed", "rejected"}
        for row in self.status_history:
            new_status = (getattr(row, "new_status", "") or "").strip().lower()
            note = (getattr(row, "note", None) or "").strip()
            if new_status in closing_statuses and note:
                return note
        return "-"

    @property
    def elapsed_label(self) -> str:
        start = self.created_at
        end = self.closed_at or utc_now()
        if not start:
            return "-"
        delta = end - start
        total_seconds = max(int(delta.total_seconds()), 0)
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        if days:
            return f"{days} g {hours} sa"
        if hours:
            return f"{hours} sa {minutes} dk"
        return f"{minutes} dk"

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SupportTicket {self.ticket_no}>"


class SupportTicketMessage(TimestampMixin, db.Model):
    __tablename__ = "support_ticket_messages"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message_type = db.Column(db.String(30), nullable=False, default="comment", index=True)
    message = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, nullable=False, default=False, index=True)

    ticket = db.relationship("SupportTicket", back_populates="messages")
    user = db.relationship("User", foreign_keys=[user_id])


class SupportTicketAttachment(TimestampMixin, db.Model):
    __tablename__ = "support_ticket_attachments"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    mime_type = db.Column(db.String(120), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    attachment_type = db.Column(db.String(30), nullable=False, default="document", index=True)

    ticket = db.relationship("SupportTicket", back_populates="attachments")
    uploaded_by = db.relationship("User", foreign_keys=[uploaded_by_user_id])


class SupportTicketStatusHistory(TimestampMixin, db.Model):
    __tablename__ = "support_ticket_status_history"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = db.Column(db.String(30), nullable=True)
    new_status = db.Column(db.String(30), nullable=False, index=True)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    note = db.Column(db.String(500), nullable=True)

    ticket = db.relationship("SupportTicket", back_populates="status_history")
    changed_by = db.relationship("User", foreign_keys=[changed_by_user_id])


class SupportFeedbackRating(TimestampMixin, db.Model):
    __tablename__ = "support_feedback_ratings"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)
    feedback_note = db.Column(db.String(500), nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    ticket = db.relationship("SupportTicket", back_populates="feedback_ratings")
    created_by = db.relationship("User", foreign_keys=[created_by_user_id])


class SupportHelpArticle(TimestampMixin, db.Model):
    __tablename__ = "support_help_articles"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(160), nullable=False, unique=True, index=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    summary = db.Column(db.String(500), nullable=True)
    category_slug = db.Column(db.String(80), nullable=False, index=True)
    role_slugs_text = db.Column(db.Text, nullable=True)
    tags_text = db.Column(db.Text, nullable=True)
    content_text = db.Column(db.Text, nullable=True)
    steps_text = db.Column(db.Text, nullable=True)
    notes_text = db.Column(db.Text, nullable=True)
    related_slugs_text = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0, index=True)
    is_published = db.Column(db.Boolean, nullable=False, default=True, index=True)
    is_featured = db.Column(db.Boolean, nullable=False, default=False, index=True)
    source_type = db.Column(db.String(30), nullable=False, default="manual", index=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    created_by = db.relationship("User", foreign_keys=[created_by_user_id])
    updated_by = db.relationship("User", foreign_keys=[updated_by_user_id])

    @staticmethod
    def _split_csv(raw: str | None) -> list[str]:
        return [item.strip() for item in (raw or "").split(",") if item and item.strip()]

    @property
    def role_slugs(self) -> list[str]:
        return self._split_csv(self.role_slugs_text)

    @property
    def tags(self) -> list[str]:
        return self._split_csv(self.tags_text)

    @property
    def related_slugs(self) -> list[str]:
        return self._split_csv(self.related_slugs_text)

    def set_role_slugs(self, values: list[str]) -> None:
        self.role_slugs_text = ", ".join(dict.fromkeys([value.strip() for value in values if value and value.strip()]))

    def set_tags(self, values: list[str]) -> None:
        self.tags_text = ", ".join(dict.fromkeys([value.strip() for value in values if value and value.strip()]))

    def set_related_slugs(self, values: list[str]) -> None:
        self.related_slugs_text = ", ".join(dict.fromkeys([value.strip() for value in values if value and value.strip()]))

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SupportHelpArticle {self.slug}>"