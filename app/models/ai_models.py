from __future__ import annotations



from app.extensions import db
from app.model_mixins import OwnershipMixin, TimestampMixin


class AIRequestLog(TimestampMixin, db.Model):
    __tablename__ = "ai_request_logs"

    id = db.Column(db.Integer, primary_key=True)
    module_type = db.Column(db.String(50), nullable=False, index=True)
    feature_type = db.Column(db.String(50), nullable=False, index=True)

    target_table = db.Column(db.String(100), nullable=True, index=True)
    target_id = db.Column(db.Integer, nullable=True, index=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    request_text = db.Column(db.Text, nullable=True)
    response_text = db.Column(db.Text, nullable=True)

    provider_name = db.Column(db.String(100), nullable=True)
    model_name = db.Column(db.String(100), nullable=True)
    prompt_version = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(30), nullable=False, default="completed", index=True)

    latency_ms = db.Column(db.Integer, nullable=True)
    token_in = db.Column(db.Integer, nullable=True)
    token_out = db.Column(db.Integer, nullable=True)

    was_masked = db.Column(db.Boolean, nullable=False, default=True)
    was_user_visible = db.Column(db.Boolean, nullable=False, default=True)
    error_message = db.Column(db.Text, nullable=True)

    user = db.relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        db.Index("ix_ai_request_logs_module_target", "module_type", "target_table", "target_id"),
    )


class AIRecommendation(TimestampMixin, OwnershipMixin, db.Model):
    __tablename__ = "ai_recommendations"

    id = db.Column(db.Integer, primary_key=True)
    module_type = db.Column(db.String(50), nullable=False, index=True)
    target_table = db.Column(db.String(100), nullable=False, index=True)
    target_id = db.Column(db.Integer, nullable=False, index=True)

    recommendation_type = db.Column(db.String(50), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=True)

    severity = db.Column(db.String(20), nullable=True, default="info", index=True)
    status = db.Column(db.String(30), nullable=False, default="open", index=True)

    ai_request_log_id = db.Column(
        db.Integer,
        db.ForeignKey("ai_request_logs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)

    ai_request_log = db.relationship("AIRequestLog", foreign_keys=[ai_request_log_id])
    reviewed_by_user = db.relationship("User", foreign_keys=[reviewed_by_user_id])

    __table_args__ = (
        db.Index("ix_ai_recommendations_target", "module_type", "target_table", "target_id"),
    )


class AIFeedbackLog(TimestampMixin, db.Model):
    __tablename__ = "ai_feedback_logs"

    id = db.Column(db.Integer, primary_key=True)
    ai_request_log_id = db.Column(
        db.Integer,
        db.ForeignKey("ai_request_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    feedback_type = db.Column(db.String(30), nullable=False, index=True)
    feedback_note = db.Column(db.Text, nullable=True)

    ai_request_log = db.relationship("AIRequestLog", foreign_keys=[ai_request_log_id])
    user = db.relationship("User", foreign_keys=[user_id])


class AIRedactionRule(TimestampMixin, OwnershipMixin, db.Model):
    __tablename__ = "ai_redaction_rules"

    id = db.Column(db.Integer, primary_key=True)
    module_type = db.Column(db.String(50), nullable=False, index=True)
    field_name = db.Column(db.String(100), nullable=False, index=True)
    redaction_type = db.Column(db.String(50), nullable=False)
    replacement_text = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    __table_args__ = (
        db.UniqueConstraint("module_type", "field_name", name="uq_ai_redaction_rules_module_field"),
    )


class AISummaryCache(TimestampMixin, db.Model):
    __tablename__ = "ai_summary_cache"

    id = db.Column(db.Integer, primary_key=True)
    module_type = db.Column(db.String(50), nullable=False, index=True)
    target_table = db.Column(db.String(100), nullable=False, index=True)
    target_id = db.Column(db.Integer, nullable=False, index=True)

    summary_kind = db.Column(db.String(50), nullable=False, index=True)
    summary_text = db.Column(db.Text, nullable=False)

    source_hash = db.Column(db.String(128), nullable=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=True, index=True)

    __table_args__ = (
        db.UniqueConstraint(
            "module_type",
            "target_table",
            "target_id",
            "summary_kind",
            name="uq_ai_summary_cache_target_kind",
        ),
    )