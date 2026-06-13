from app.core.datetime_utils import utc_now
from datetime import datetime

from app.extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
        index=True,
    )


class CommunicationNotificationPreference(db.Model, TimestampMixin):
    __tablename__ = "communication_notification_preferences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    in_app_enabled = db.Column(db.Boolean, nullable=False, default=True)
    email_enabled = db.Column(db.Boolean, nullable=False, default=False)
    daily_digest_enabled = db.Column(db.Boolean, nullable=False, default=False)
    weekly_digest_enabled = db.Column(db.Boolean, nullable=False, default=True)
    digest_hour = db.Column(db.Integer, nullable=False, default=9)
    quiet_hours_enabled = db.Column(db.Boolean, nullable=False, default=False)
    quiet_hours_start = db.Column(db.Integer, nullable=False, default=20)
    quiet_hours_end = db.Column(db.Integer, nullable=False, default=8)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("communication_notification_preferences", lazy="dynamic"),
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", name="uq_comm_notification_preference_user"),
    )


class CommunicationDigestJob(db.Model, TimestampMixin):
    __tablename__ = "communication_digest_jobs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    digest_type = db.Column(db.String(20), nullable=False, default="daily", index=True)
    period_label = db.Column(db.String(120), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="queued", index=True)
    scheduled_for = db.Column(db.DateTime, nullable=True, index=True)
    executed_at = db.Column(db.DateTime, nullable=True, index=True)
    payload_json = db.Column(db.JSON, nullable=True)
    result_summary = db.Column(db.Text, nullable=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("communication_digest_jobs", lazy="dynamic"),
    )


class CommunicationEscalationRule(db.Model, TimestampMixin):
    __tablename__ = "communication_escalation_rules"

    id = db.Column(db.Integer, primary_key=True)
    module_name = db.Column(db.String(50), nullable=False, default="support", index=True)
    priority = db.Column(db.String(20), nullable=False, default="normal", index=True)
    trigger_type = db.Column(db.String(30), nullable=False, default="sla_breach", index=True)
    threshold_hours = db.Column(db.Integer, nullable=False, default=24)
    target_role = db.Column(db.String(50), nullable=True, index=True)
    target_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    notify_template = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    target_user = db.relationship(
        "User",
        foreign_keys=[target_user_id],
        backref=db.backref("communication_escalation_rules", lazy="dynamic"),
    )


class CommunicationRetentionPolicy(db.Model, TimestampMixin):
    __tablename__ = "communication_retention_policies"

    id = db.Column(db.Integer, primary_key=True)
    data_scope = db.Column(db.String(50), nullable=False, index=True)
    keep_days = db.Column(db.Integer, nullable=False, default=365)
    archive_after_days = db.Column(db.Integer, nullable=True)
    anonymize_after_days = db.Column(db.Integer, nullable=True)
    purge_after_days = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    notes = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("data_scope", name="uq_comm_retention_scope"),
    )


class CommunicationOperationHealth(db.Model, TimestampMixin):
    __tablename__ = "communication_operation_health"

    id = db.Column(db.Integer, primary_key=True)
    check_name = db.Column(db.String(100), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="ok", index=True)
    metric_value = db.Column(db.String(100), nullable=True)
    details = db.Column(db.Text, nullable=True)
    checked_at = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)


class CommunicationAutomationLog(db.Model, TimestampMixin):
    __tablename__ = "communication_automation_logs"

    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(db.String(50), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="success", index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    target_table = db.Column(db.String(100), nullable=True, index=True)
    target_id = db.Column(db.Integer, nullable=True, index=True)
    summary = db.Column(db.String(255), nullable=True)
    payload_json = db.Column(db.JSON, nullable=True)
    executed_at = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)

    actor = db.relationship(
        "User",
        foreign_keys=[actor_user_id],
        backref=db.backref("communication_automation_logs", lazy="dynamic"),
    )