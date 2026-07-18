
"""Kurumsal geri bildirim veri modelleri.

Bu dosya mevcut survey yapisini bozmadan, daha kurumsal ve surekli calisan
nabiz / geri bildirim / aksiyon omurgasi kurmak icin eklendi.
"""
from __future__ import annotations

from datetime import date

from app.core.datetime_utils import utc_now

from .base import TimestampMixin, db


class FeedbackCampaign(TimestampMixin, db.Model):
    __tablename__ = "feedback_campaigns"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    campaign_type = db.Column(db.String(40), nullable=False, default="survey", index=True)
    status = db.Column(db.String(30), nullable=False, default="draft", index=True)

    target_scope = db.Column(db.String(30), nullable=False, default="all", index=True)
    organization_unit_id = db.Column(db.Integer, db.ForeignKey("organization_units.id"), nullable=True, index=True)

    is_anonymous = db.Column(db.Boolean, nullable=False, default=False)
    allow_multiple_submissions = db.Column(db.Boolean, nullable=False, default=False)
    allow_comment = db.Column(db.Boolean, nullable=False, default=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    start_at = db.Column(db.DateTime, nullable=True, index=True)
    end_at = db.Column(db.DateTime, nullable=True, index=True)
    published_at = db.Column(db.DateTime, nullable=True)

    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    created_by = db.relationship("User", foreign_keys=[created_by_user_id])
    organization_unit = db.relationship("OrganizationUnit", foreign_keys=[organization_unit_id])

    questions = db.relationship(
        "FeedbackQuestion",
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    assignments = db.relationship(
        "FeedbackCampaignAssignment",
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    submissions = db.relationship(
        "FeedbackSubmission",
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    action_plans = db.relationship(
        "FeedbackActionPlan",
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<FeedbackCampaign id={self.id} title={self.title!r}>"


class FeedbackQuestion(TimestampMixin, db.Model):
    __tablename__ = "feedback_questions"

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("feedback_campaigns.id"), nullable=False, index=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(30), nullable=False, default="scale_1_5", index=True)
    is_required = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=1)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    campaign = db.relationship("FeedbackCampaign", back_populates="questions")
    options = db.relationship(
        "FeedbackQuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    answers = db.relationship(
        "FeedbackAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<FeedbackQuestion id={self.id} campaign={self.campaign_id}>"


class FeedbackQuestionOption(TimestampMixin, db.Model):
    __tablename__ = "feedback_question_options"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("feedback_questions.id"), nullable=False, index=True)
    option_text = db.Column(db.String(255), nullable=False)
    option_value = db.Column(db.String(100), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=1)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    question = db.relationship("FeedbackQuestion", back_populates="options")

    def __repr__(self):
        return f"<FeedbackQuestionOption id={self.id} question={self.question_id}>"


class FeedbackCampaignAssignment(TimestampMixin, db.Model):
    __tablename__ = "feedback_campaign_assignments"

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("feedback_campaigns.id"), nullable=False, index=True)
    target_type = db.Column(db.String(30), nullable=False, default="all", index=True)
    target_value = db.Column(db.String(255), nullable=True, index=True)

    campaign = db.relationship("FeedbackCampaign", back_populates="assignments")

    def __repr__(self):
        return f"<FeedbackCampaignAssignment id={self.id} campaign={self.campaign_id} target={self.target_type}>"


class FeedbackSubmission(TimestampMixin, db.Model):
    __tablename__ = "feedback_submissions"

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("feedback_campaigns.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    organization_unit_id = db.Column(db.Integer, db.ForeignKey("organization_units.id"), nullable=True, index=True)

    submitted_at = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)
    is_completed = db.Column(db.Boolean, nullable=False, default=True, index=True)
    anonymous_token = db.Column(db.String(100), nullable=True, index=True)

    campaign = db.relationship("FeedbackCampaign", back_populates="submissions")
    user = db.relationship("User", foreign_keys=[user_id])
    organization_unit = db.relationship("OrganizationUnit", foreign_keys=[organization_unit_id])
    answers = db.relationship(
        "FeedbackAnswer",
        back_populates="submission",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<FeedbackSubmission id={self.id} campaign={self.campaign_id}>"


class FeedbackAnswer(TimestampMixin, db.Model):
    __tablename__ = "feedback_answers"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("feedback_submissions.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("feedback_questions.id"), nullable=False, index=True)
    selected_option_id = db.Column(db.Integer, db.ForeignKey("feedback_question_options.id"), nullable=True)
    answer_text = db.Column(db.Text, nullable=True)
    answer_number = db.Column(db.Float, nullable=True)

    submission = db.relationship("FeedbackSubmission", back_populates="answers")
    question = db.relationship("FeedbackQuestion", back_populates="answers")
    selected_option = db.relationship("FeedbackQuestionOption", foreign_keys=[selected_option_id])

    def __repr__(self):
        return f"<FeedbackAnswer id={self.id} submission={self.submission_id}>"


class FeedbackPulseEntry(TimestampMixin, db.Model):
    __tablename__ = "feedback_pulse_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    organization_unit_id = db.Column(db.Integer, db.ForeignKey("organization_units.id"), nullable=True, index=True)
    entry_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    mood_value = db.Column(db.Integer, nullable=False, index=True)
    mood_label = db.Column(db.String(100), nullable=False)
    short_note = db.Column(db.Text, nullable=True)
    is_anonymous = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", foreign_keys=[user_id])
    organization_unit = db.relationship("OrganizationUnit", foreign_keys=[organization_unit_id])

    __table_args__ = (
        db.UniqueConstraint("user_id", "entry_date", name="uq_feedback_pulse_user_date"),
    )

    def __repr__(self):
        return f"<FeedbackPulseEntry user={self.user_id} date={self.entry_date}>"


class FeedbackActionPlan(TimestampMixin, db.Model):
    __tablename__ = "feedback_action_plans"

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("feedback_campaigns.id"), nullable=True, index=True)
    organization_unit_id = db.Column(db.Integer, db.ForeignKey("organization_units.id"), nullable=True, index=True)
    assigned_manager_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(20), nullable=False, default="medium", index=True)
    status = db.Column(db.String(20), nullable=False, default="open", index=True)
    due_date = db.Column(db.Date, nullable=True)
    resolution_note = db.Column(db.Text, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    campaign = db.relationship("FeedbackCampaign", back_populates="action_plans")
    organization_unit = db.relationship("OrganizationUnit", foreign_keys=[organization_unit_id])
    assigned_manager = db.relationship("User", foreign_keys=[assigned_manager_id])
    created_by = db.relationship("User", foreign_keys=[created_by_user_id])

    def __repr__(self):
        return f"<FeedbackActionPlan id={self.id} status={self.status}>"