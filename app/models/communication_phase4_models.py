from __future__ import annotations

from app.core.datetime_utils import utc_now

from app.extensions import db
from app.models.base import TimestampMixin


class CommunicationExecutiveReport(TimestampMixin, db.Model):
    __tablename__ = "communication_executive_reports"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    report_type = db.Column(db.String(50), nullable=False, default="weekly_summary", index=True)
    period_label = db.Column(db.String(120), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="draft", index=True)

    summary_text = db.Column(db.Text, nullable=True)
    metrics_json = db.Column(db.JSON, nullable=True)
    recommendations_json = db.Column(db.JSON, nullable=True)

    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    approved_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    approved_at = db.Column(db.DateTime, nullable=True, index=True)

    created_by = db.relationship("User", foreign_keys=[created_by_user_id])
    approved_by = db.relationship("User", foreign_keys=[approved_by_user_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CommunicationExecutiveReport {self.id} {self.report_type}>"


class CommunicationReportExportLog(TimestampMixin, db.Model):
    __tablename__ = "communication_report_export_logs"

    id = db.Column(db.Integer, primary_key=True)
    export_type = db.Column(db.String(50), nullable=False, index=True)
    export_format = db.Column(db.String(20), nullable=False, default="csv", index=True)
    file_name = db.Column(db.String(255), nullable=True)

    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    criteria_json = db.Column(db.JSON, nullable=True)
    row_count = db.Column(db.Integer, nullable=False, default=0)

    created_by = db.relationship("User", foreign_keys=[created_by_user_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CommunicationReportExportLog {self.export_type}:{self.export_format}>"


class CommunicationGovernanceReview(TimestampMixin, db.Model):
    __tablename__ = "communication_governance_reviews"

    id = db.Column(db.Integer, primary_key=True)
    review_type = db.Column(db.String(50), nullable=False, index=True)  # bulletin / survey / support / report
    target_id = db.Column(db.Integer, nullable=False, index=True)
    decision = db.Column(db.String(30), nullable=False, default="pending", index=True)  # pending / approved / revision / rejected
    review_note = db.Column(db.Text, nullable=True)

    requested_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    reviewed_at = db.Column(db.DateTime, nullable=True, index=True)

    requested_by = db.relationship("User", foreign_keys=[requested_by_user_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_user_id])

    __table_args__ = (
        db.Index("ix_comm_governance_review_target", "review_type", "target_id"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CommunicationGovernanceReview {self.review_type}:{self.target_id}>"


class CommunicationDailyMetric(TimestampMixin, db.Model):
    __tablename__ = "communication_daily_metrics"

    id = db.Column(db.Integer, primary_key=True)
    metric_date = db.Column(db.Date, nullable=False, index=True)
    metric_group = db.Column(db.String(50), nullable=False, index=True)  # notifications / bulletins / surveys / support
    metric_name = db.Column(db.String(120), nullable=False, index=True)
    metric_value = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    unit_label = db.Column(db.String(30), nullable=True)
    snapshot_json = db.Column(db.JSON, nullable=True)

    captured_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    captured_at = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)

    captured_by = db.relationship("User", foreign_keys=[captured_by_user_id])

    __table_args__ = (
        db.UniqueConstraint(
            "metric_date",
            "metric_group",
            "metric_name",
            name="uq_comm_daily_metric_name",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CommunicationDailyMetric {self.metric_group}:{self.metric_name}>"