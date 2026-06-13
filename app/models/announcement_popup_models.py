
"""BYS360 video destekli pop-up duyuru modelleri.

Faz 3 kapsamı:
- announcements: duyurunun ana kaydı
- announcement_reads: kullanıcı bazlı görüldü/okundu/kapatıldı geçmişi
- dashboard runtime pop-up akışı

Not: Kolon adları Faz 1 şema uygulayıcısı ve Alembic migration ile uyumludur.
Kod tarafında created_by / updated_by alan adları korunur; veritabanında
created_by_user_id / updated_by_user_id kolonları kullanılır.
"""
from __future__ import annotations

from .base import TimestampMixin, db


class Announcement(TimestampMixin, db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)

    announcement_type = db.Column(db.String(30), nullable=False, default="info", index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    is_required = db.Column(db.Boolean, nullable=False, default=False, index=True)
    show_rule = db.Column(db.String(30), nullable=False, default="once", index=True)

    target_scope = db.Column(db.String(30), nullable=False, default="all", index=True)
    target_role = db.Column(db.String(80), nullable=True, index=True)
    target_unit_id = db.Column(db.Integer, db.ForeignKey("organization_units.id", ondelete="SET NULL"), nullable=True, index=True)

    publish_start_at = db.Column(db.DateTime, nullable=True, index=True)
    publish_end_at = db.Column(db.DateTime, nullable=True, index=True)
    button_text = db.Column(db.String(80), nullable=False, default="Okudum")

    media_type = db.Column(db.String(30), nullable=False, default="none", index=True)
    media_url = db.Column(db.Text, nullable=True)
    media_file_path = db.Column(db.String(500), nullable=True)
    cover_image_path = db.Column(db.String(500), nullable=True)
    cta_text = db.Column(db.String(120), nullable=True)
    cta_url = db.Column(db.String(500), nullable=True)

    created_by = db.Column("created_by_user_id", db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by = db.Column("updated_by_user_id", db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    creator = db.relationship("User", foreign_keys=[created_by])
    updater = db.relationship("User", foreign_keys=[updated_by])
    target_unit = db.relationship("OrganizationUnit", foreign_keys=[target_unit_id])
    reads = db.relationship("AnnouncementRead", back_populates="announcement", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def type_label(self) -> str:
        return {
            "info": "Bilgilendirme",
            "warning": "Uyarı",
            "important": "Önemli",
            "maintenance": "Bakım",
        }.get((self.announcement_type or "info").lower(), self.announcement_type or "Bilgilendirme")

    @property
    def media_label(self) -> str:
        return {
            "none": "Yok",
            "youtube": "YouTube",
            "vimeo": "Vimeo",
            "dailymotion": "Dailymotion",
            "upload_video": "Kurum Videosu",
            "image": "Görsel",
            "pdf": "PDF",
        }.get((self.media_type or "none").lower(), self.media_type or "Yok")


class AnnouncementRead(TimestampMixin, db.Model):
    __tablename__ = "announcement_reads"

    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    first_seen_at = db.Column(db.DateTime, nullable=True)
    last_seen_at = db.Column(db.DateTime, nullable=True)
    dismissed_at = db.Column(db.DateTime, nullable=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    seen_count = db.Column(db.Integer, nullable=False, default=0)

    ip_address = db.Column(db.String(80), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)

    announcement = db.relationship("Announcement", back_populates="reads")
    user = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("announcement_id", "user_id", name="uq_announcement_reads_announcement_user"),
    )
