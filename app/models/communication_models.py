"""Mesajlasma, anket ve geri bildirim akisi modelleri."""

from datetime import datetime

from app.core.datetime_utils import utc_now

from .base import TimestampMixin, db
import logging
logger = logging.getLogger(__name__)


_FEEDBACK_RESPONSE_CACHE_MISSING = object()


class FeedbackRequest(db.Model):
    __tablename__ = "feedback_requests"

    id = db.Column(db.Integer, primary_key=True)

    evaluation_id = db.Column(
        db.Integer,
        db.ForeignKey("performance_evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_id = db.Column(
        db.Integer,
        db.ForeignKey("performance_periods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    level_1_manager_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    level_2_manager_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    level_3_manager_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="bekliyor", index=True)

    requested_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    scheduled_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    scheduled_meeting_id = db.Column(
        db.Integer,
        db.ForeignKey("feedback_meetings.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    closed_at = db.Column(db.DateTime, nullable=True)

    evaluation = db.relationship("PerformanceEvaluation", foreign_keys=[evaluation_id], backref="feedback_requests")
    period = db.relationship("PerformancePeriod", foreign_keys=[period_id], backref="feedback_requests")

    employee = db.relationship("User", foreign_keys=[employee_id])
    level_1_manager = db.relationship("User", foreign_keys=[level_1_manager_id])
    level_2_manager = db.relationship("User", foreign_keys=[level_2_manager_id])
    level_3_manager = db.relationship("User", foreign_keys=[level_3_manager_id])
    scheduled_by = db.relationship("User", foreign_keys=[scheduled_by_id])

    @property
    def meeting(self):
        try:
            return FeedbackMeeting.query.filter_by(feedback_request_id=self.id).first()
        except Exception:
            logger.exception("BYS360 V6C guarded exception | file=app/models/communication_models.py | line=86")
            return None

    @property
    def response(self):
        cached = getattr(self, "_response_preview_cache", _FEEDBACK_RESPONSE_CACHE_MISSING)
        if cached is not _FEEDBACK_RESPONSE_CACHE_MISSING:
            return cached
        try:
            log = (
                MailLog.query
                .filter_by(related_feedback_request_id=self.id, mail_type="feedback_response")
                .order_by(MailLog.sent_at.desc(), MailLog.id.desc())
                .first()
            )
            cached = (log.body_preview or "").strip() if log and log.body_preview else None
        except Exception:
            logger.exception("BYS360 V6C guarded exception | file=app/models/communication_models.py | line=102")
            cached = None
        self._response_preview_cache = cached
        return cached

    def __repr__(self):
        return f"<FeedbackRequest id={self.id} employee_id={self.employee_id} status={self.status}>"


class MailLog(db.Model):
    __tablename__ = "mail_logs"

    id = db.Column(db.Integer, primary_key=True)
    mail_type = db.Column(db.String(50), nullable=False, index=True)

    related_period_id = db.Column(
        db.Integer,
        db.ForeignKey("performance_periods.id", ondelete="SET NULL"),
        nullable=True,
    )
    related_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    related_feedback_request_id = db.Column(
        db.Integer,
        db.ForeignKey("feedback_requests.id", ondelete="SET NULL"),
        nullable=True,
    )

    recipient_email = db.Column(db.String(255), nullable=False, index=True)
    subject = db.Column(db.String(255), nullable=False)
    body_preview = db.Column(db.Text, nullable=True)

    sent_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    sent_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    is_success = db.Column(db.Boolean, nullable=False, default=True)
    error_message = db.Column(db.Text, nullable=True)

    period = db.relationship("PerformancePeriod", foreign_keys=[related_period_id])
    user = db.relationship("User", foreign_keys=[related_user_id])
    feedback_request = db.relationship("FeedbackRequest", foreign_keys=[related_feedback_request_id])
    sent_by = db.relationship("User", foreign_keys=[sent_by_id])

    def __repr__(self):
        return f"<MailLog id={self.id} type={self.mail_type} recipient={self.recipient_email}>"


class EvaluationPublishLog(db.Model):
    __tablename__ = "evaluation_publish_logs"

    id = db.Column(db.Integer, primary_key=True)

    evaluation_id = db.Column(
        db.Integer,
        db.ForeignKey("performance_evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_id = db.Column(
        db.Integer,
        db.ForeignKey("performance_periods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action = db.Column(db.String(20), nullable=False)
    acted_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    acted_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    evaluation = db.relationship("PerformanceEvaluation", foreign_keys=[evaluation_id])
    employee = db.relationship("User", foreign_keys=[employee_id])
    period = db.relationship("PerformancePeriod", foreign_keys=[period_id])
    acted_by = db.relationship("User", foreign_keys=[acted_by_id])


class FeedbackMeeting(db.Model):
    __tablename__ = "feedback_meetings"

    id = db.Column(db.Integer, primary_key=True)
    feedback_request_id = db.Column(
        db.Integer,
        db.ForeignKey("feedback_requests.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    manager_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    meeting_date = db.Column(db.Date, nullable=False)
    meeting_start = db.Column(db.Time, nullable=False)
    meeting_end = db.Column(db.Time, nullable=False)

    location = db.Column(db.String(255), nullable=True)
    meeting_type = db.Column(db.String(30), nullable=False, default="yuz_yuze")
    note = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="planlandi")
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    feedback_request = db.relationship("FeedbackRequest", foreign_keys=[feedback_request_id])
    employee = db.relationship("User", foreign_keys=[employee_id])
    manager = db.relationship("User", foreign_keys=[manager_id])

class MessageThread(TimestampMixin, db.Model):
    __tablename__ = "message_threads"

    id = db.Column(db.Integer, primary_key=True)
    thread_type = db.Column(db.String(30), nullable=False, default="direct", index=True)
    subject = db.Column(db.String(255), nullable=True)
    badge_label = db.Column(db.String(120), nullable=True)
    icon_name = db.Column(db.String(100), nullable=True)
    accent_color = db.Column(db.String(20), nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    last_message_at = db.Column(db.DateTime, nullable=True, index=True)

    created_by = db.relationship("User", foreign_keys=[created_by_user_id], back_populates="created_message_threads")
    participants = db.relationship(
        "MessageThreadParticipant",
        back_populates="thread",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    messages = db.relationship(
        "Message",
        back_populates="thread",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<MessageThread id={self.id} type={self.thread_type}>"


class MessageThreadParticipant(TimestampMixin, db.Model):
    __tablename__ = "message_thread_participants"

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("message_threads.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    joined_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    left_at = db.Column(db.DateTime, nullable=True)
    is_muted = db.Column(db.Boolean, nullable=False, default=False)
    is_archived = db.Column(db.Boolean, nullable=False, default=False)
    is_pinned = db.Column(db.Boolean, nullable=False, default=False, index=True)
    last_read_message_id = db.Column(db.Integer, db.ForeignKey("messages.id"), nullable=True)
    last_read_at = db.Column(db.DateTime, nullable=True, index=True)

    thread = db.relationship("MessageThread", back_populates="participants")
    user = db.relationship("User", foreign_keys=[user_id])
    last_read_message = db.relationship("Message", foreign_keys=[last_read_message_id])

    __table_args__ = (
        db.UniqueConstraint("thread_id", "user_id", name="uq_message_thread_participant"),
    )

    def __repr__(self):
        return f"<MessageThreadParticipant thread={self.thread_id} user={self.user_id}>"

class Message(TimestampMixin, db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("message_threads.id"), nullable=False, index=True)
    sender_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    body = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(30), nullable=False, default="text", index=True)
    sent_at = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)
    edited_at = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False, index=True)

    thread = db.relationship("MessageThread", back_populates="messages")
    sender = db.relationship("User", foreign_keys=[sender_user_id], back_populates="sent_messages", overlaps="sent_messages")

    def __repr__(self):
        return f"<Message id={self.id} thread={self.thread_id}>"


class MessageReaction(TimestampMixin, db.Model):
    __tablename__ = "message_reactions"

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(
        db.Integer,
        db.ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reaction_value = db.Column(db.String(16), nullable=False, index=True)

    message = db.relationship(
        "Message",
        backref=db.backref("reactions", lazy="dynamic", cascade="all, delete-orphan"),
    )
    user = db.relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        db.UniqueConstraint("message_id", "user_id", name="uq_message_reaction_user_message"),
    )

    def __repr__(self):
        return f"<MessageReaction message={self.message_id} user={self.user_id} value={self.reaction_value}>"



class MessageComment(TimestampMixin, db.Model):
    __tablename__ = "message_comments"

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(
        db.Integer,
        db.ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    body = db.Column(db.Text, nullable=False)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False, index=True)
    edited_at = db.Column(db.DateTime, nullable=True)

    message = db.relationship(
        "Message",
        backref=db.backref("comments", lazy="dynamic", cascade="all, delete-orphan"),
    )
    user = db.relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<MessageComment message={self.message_id} user={self.user_id}>"

# BYS360_PHASE4A_MESSAGE_COMMENT_MODEL


class MessageTypingState(TimestampMixin, db.Model):
    __tablename__ = "message_typing_states"

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(
        db.Integer,
        db.ForeignKey("message_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    preview_text = db.Column(db.String(120), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    last_activity_at = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)

    thread = db.relationship(
        "MessageThread",
        backref=db.backref("typing_states", lazy="dynamic", cascade="all, delete-orphan"),
    )
    user = db.relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        db.UniqueConstraint("thread_id", "user_id", name="uq_message_typing_state_thread_user"),
    )

    def __repr__(self):
        return f"<MessageTypingState thread={self.thread_id} user={self.user_id}>"


class Notification(TimestampMixin, db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=True)

    notification_type = db.Column(db.String(50), nullable=False, index=True)
    source_type = db.Column(db.String(50), nullable=True, index=True)
    source_id = db.Column(db.Integer, nullable=True, index=True)
    link_url = db.Column(db.String(500), nullable=True)

    priority = db.Column(db.String(20), nullable=False, default="normal", index=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", foreign_keys=[user_id], back_populates="notifications", overlaps="notifications")

    def __repr__(self):
        return f"<Notification id={self.id} user={self.user_id} type={self.notification_type}>"

class Survey(TimestampMixin, db.Model):
    __tablename__ = "surveys"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    survey_type = db.Column(db.String(50), nullable=False, default="kurum_ici", index=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    is_anonymous = db.Column(db.Boolean, nullable=False, default=False)
    allow_multiple_submissions = db.Column(db.Boolean, nullable=False, default=False)

    start_at = db.Column(db.DateTime, nullable=True, index=True)
    end_at = db.Column(db.DateTime, nullable=True, index=True)
    status = db.Column(db.String(30), nullable=False, default="draft", index=True)

    created_by = db.relationship("User", foreign_keys=[created_by_user_id], back_populates="created_surveys", overlaps="created_surveys")
    questions = db.relationship(
        "SurveyQuestion",
        back_populates="survey",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    assignments = db.relationship(
        "SurveyAssignment",
        back_populates="survey",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    responses = db.relationship(
        "SurveyResponse",
        back_populates="survey",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Survey id={self.id} title={self.title}>"

class SurveyQuestion(TimestampMixin, db.Model):
    __tablename__ = "survey_questions"

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("surveys.id"), nullable=False, index=True)

    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(30), nullable=False, index=True)
    is_required = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=1)
    # Live-core compatibility note:
    # The current production-aligned survey schema keeps only the phase-1 columns.
    # Optional phase-2 authoring fields such as helper text / conditional logic are
    # handled in routes/templates with safe defaults and must not be mapped here,
    # otherwise PostgreSQL will try to read non-existent columns.

    survey = db.relationship("Survey", back_populates="questions")
    options = db.relationship(
        "SurveyQuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    answers = db.relationship(
        "SurveyAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<SurveyQuestion id={self.id} survey={self.survey_id}>"

class SurveyQuestionOption(TimestampMixin, db.Model):
    __tablename__ = "survey_question_options"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("survey_questions.id"), nullable=False, index=True)

    option_text = db.Column(db.String(255), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=1)

    question = db.relationship("SurveyQuestion", back_populates="options")

    def __repr__(self):
        return f"<SurveyQuestionOption id={self.id} question={self.question_id}>"

class SurveyAssignment(TimestampMixin, db.Model):
    __tablename__ = "survey_assignments"

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("surveys.id"), nullable=False, index=True)

    target_type = db.Column(db.String(30), nullable=False, index=True)   # all, user, role, unit
    target_value = db.Column(db.String(255), nullable=True, index=True)
    assigned_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    survey = db.relationship("Survey", back_populates="assignments")

    responses = db.relationship(
        "SurveyResponse",
        back_populates="assignment",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<SurveyAssignment id={self.id} survey={self.survey_id} target={self.target_type}>"

class SurveyResponse(TimestampMixin, db.Model):
    __tablename__ = "survey_responses"

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("surveys.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("survey_assignments.id"), nullable=True, index=True)

    submitted_at = db.Column(db.DateTime, nullable=True, index=True)
    is_completed = db.Column(db.Boolean, nullable=False, default=False, index=True)
    anonymous_token = db.Column(db.String(100), nullable=True, index=True)

    survey = db.relationship("Survey", back_populates="responses")
    user = db.relationship("User", foreign_keys=[user_id], back_populates="survey_responses", overlaps="survey_responses")
    assignment = db.relationship("SurveyAssignment", back_populates="responses")
    answers = db.relationship(
        "SurveyAnswer",
        back_populates="response",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<SurveyResponse id={self.id} survey={self.survey_id}>"

class SurveyAnswer(TimestampMixin, db.Model):
    __tablename__ = "survey_answers"

    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.Integer, db.ForeignKey("survey_responses.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("survey_questions.id"), nullable=False, index=True)

    selected_option_id = db.Column(db.Integer, db.ForeignKey("survey_question_options.id"), nullable=True)
    answer_text = db.Column(db.Text, nullable=True)
    answer_number = db.Column(db.Float, nullable=True)

    response = db.relationship("SurveyResponse", back_populates="answers")
    question = db.relationship("SurveyQuestion", back_populates="answers")
    selected_option = db.relationship("SurveyQuestionOption", foreign_keys=[selected_option_id])

    def __repr__(self):
        return f"<SurveyAnswer id={self.id} response={self.response_id}>"

class MessageAttachment(TimestampMixin, db.Model):
    __tablename__ = "message_attachments"

    id = db.Column(db.Integer, primary_key=True)

    message_id = db.Column(
        db.Integer,
        db.ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True, index=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_ext = db.Column(db.String(20), nullable=True, index=True)
    mime_type = db.Column(db.String(120), nullable=True)
    file_size = db.Column(db.Integer, nullable=False, default=0)

    uploaded_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    message = db.relationship(
        "Message",
        backref=db.backref("attachments", lazy="dynamic", cascade="all, delete-orphan"),
    )

    uploaded_by = db.relationship(
        "User",
        foreign_keys=[uploaded_by_user_id],
    )

    def __repr__(self):
        return f"<MessageAttachment id={self.id} file={self.original_filename}>"
