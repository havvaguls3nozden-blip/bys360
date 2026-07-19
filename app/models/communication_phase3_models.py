from __future__ import annotations

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models.base import TimestampMixin


class CommunicationSupportSlaPolicy(TimestampMixin, db.Model):
    __tablename__ = "communication_support_sla_policies"

    id = db.Column(db.Integer, primary_key=True)
    module_name = db.Column(db.String(120), nullable=False, index=True)
    priority = db.Column(db.String(20), nullable=False, default="normal", index=True)
    first_response_target_hours = db.Column(db.Integer, nullable=False, default=24)
    resolution_target_hours = db.Column(db.Integer, nullable=False, default=72)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    created_by = db.relationship("User", foreign_keys=[created_by_user_id])

    __table_args__ = (
        db.UniqueConstraint("module_name", "priority", name="uq_comm_support_sla_module_priority"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CommunicationSupportSlaPolicy {self.module_name}:{self.priority}>"


class CommunicationSupportAssignmentLog(TimestampMixin, db.Model):
    __tablename__ = "communication_support_assignment_logs"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey("support_tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_assigned_to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    new_assigned_to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    assigned_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    note = db.Column(db.String(500), nullable=True)

    ticket = db.relationship("SupportTicket", foreign_keys=[ticket_id])
    old_assigned_to = db.relationship("User", foreign_keys=[old_assigned_to_user_id])
    new_assigned_to = db.relationship("User", foreign_keys=[new_assigned_to_user_id])
    assigned_by = db.relationship("User", foreign_keys=[assigned_by_user_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CommunicationSupportAssignmentLog ticket={self.ticket_id}>"


class CommunicationSurveyReminderLog(TimestampMixin, db.Model):
    __tablename__ = "communication_survey_reminder_logs"

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("survey_assignments.id", ondelete="SET NULL"), nullable=True, index=True)
    reminder_type = db.Column(db.String(30), nullable=False, default="in_app", index=True)
    note = db.Column(db.String(500), nullable=True)
    sent_at = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)

    survey = db.relationship("Survey", foreign_keys=[survey_id])
    user = db.relationship("User", foreign_keys=[user_id])
    assignment = db.relationship("SurveyAssignment", foreign_keys=[assignment_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CommunicationSurveyReminderLog survey={self.survey_id} user={self.user_id}>"


class CommunicationHelpArticleViewLog(TimestampMixin, db.Model):
    __tablename__ = "communication_help_article_view_logs"

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(
        db.Integer,
        db.ForeignKey("support_help_articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    search_term = db.Column(db.String(255), nullable=True, index=True)
    viewed_at = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)

    article = db.relationship("SupportHelpArticle", foreign_keys=[article_id])
    user = db.relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CommunicationHelpArticleViewLog article={self.article_id} user={self.user_id}>"