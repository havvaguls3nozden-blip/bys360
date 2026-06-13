
"""BYS360 Faz 7.1 — Geçmiş yıl karne ve puan arşivi veri modeli.

Bu model canlı performans değerlendirme sonuçlarından ayrı çalışır.
2024/2025 gibi eski puan cetvelleri manuel giriş veya Excel import ile
``performance_archived_results`` tablosuna alınır.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from .base import TimestampMixin, db


class PerformanceArchivedResult(TimestampMixin, db.Model):
    """Geçmiş yıl performans puanı / karne arşivi kaydı.

    Alan eşlemesi:
    - personel -> employee_id / employee
    - yıl -> result_year
    - dönem -> period_label
    - puan -> score
    - açıklama -> description
    - kaynak belge -> source_document, source_document_name
    - ekleyen kullanıcı -> created_by_user_id / created_by
    - eklenme tarihi -> created_at
    """

    __tablename__ = "performance_archived_results"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    result_year = db.Column(db.Integer, nullable=False, index=True)
    period_label = db.Column(db.String(120), nullable=False, index=True)
    score = db.Column(db.Numeric(5, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    source_document = db.Column(db.String(500), nullable=True)
    source_document_name = db.Column(db.String(255), nullable=True)
    source_type = db.Column(db.String(40), nullable=False, default="manual", index=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    employee = db.relationship("User", foreign_keys=[employee_id], lazy="joined")
    created_by = db.relationship("User", foreign_keys=[created_by_user_id], lazy="joined")

    __table_args__ = (
        db.CheckConstraint("score >= 0 AND score <= 100", name="ck_performance_archived_results_score_range"),
        db.Index("ix_performance_archived_results_employee_year", "employee_id", "result_year"),
        db.Index("ix_performance_archived_results_year_period", "result_year", "period_label"),
        db.Index("ix_performance_archived_results_created_by_created_at", "created_by_user_id", "created_at"),
    )

    @property
    def yil(self) -> int:
        return int(self.result_year or 0)

    @property
    def year(self) -> int:
        return self.yil

    @property
    def donem(self) -> str:
        return str(self.period_label or "")

    @property
    def puan(self) -> Decimal:
        try:
            return Decimal(str(self.score or "0")).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal("0.00")

    @property
    def score_float(self) -> float:
        try:
            return float(self.score or 0)
        except (TypeError, ValueError):
            return 0.0

    @property
    def aciklama(self) -> str:
        return str(self.description or "")

    @property
    def kaynak_belge(self) -> str:
        return str(self.source_document_name or self.source_document or "")

    @property
    def eklenme_tarihi(self):
        return self.created_at

    def to_summary_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "personel": getattr(self.employee, "full_name", None) or getattr(self.employee, "full_name_cache", None) or "-",
            "yil": self.yil,
            "donem": self.donem,
            "puan": self.score_float,
            "aciklama": self.aciklama,
            "kaynak_belge": self.kaynak_belge,
            "kaynak_belge_yolu": self.source_document,
            "kaynak_turu": self.source_type,
            "ekleyen_kullanici_id": self.created_by_user_id,
            "eklenme_tarihi": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<PerformanceArchivedResult employee={self.employee_id} "
            f"year={self.result_year} period={self.period_label!r} score={self.score}>"
        )
