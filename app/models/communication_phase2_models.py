from __future__ import annotations



from app.extensions import db
from app.models.base import TimestampMixin


class CommunicationBulletinRevision(TimestampMixin, db.Model):
    __tablename__ = "communication_bulletin_revisions"

    id = db.Column(db.Integer, primary_key=True)
    bulletin_id = db.Column(
        db.Integer,
        db.ForeignKey("communication_bulletins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_no = db.Column(db.Integer, nullable=False, default=1, index=True)

    title = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.String(500), nullable=True)
    content = db.Column(db.Text, nullable=False)
    bulletin_type = db.Column(db.String(50), nullable=False, default="duyuru")
    priority = db.Column(db.String(20), nullable=False, default="normal")
    status = db.Column(db.String(30), nullable=False, default="draft")
    change_note = db.Column(db.String(500), nullable=True)

    changed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    bulletin = db.relationship(
        "CommunicationBulletin",
        backref=db.backref(
            "revisions",
            lazy="dynamic",
            cascade="all, delete-orphan",
            order_by="CommunicationBulletinRevision.version_no.desc()",
        ),
    )
    changed_by = db.relationship("User", foreign_keys=[changed_by_user_id])

    __table_args__ = (
        db.UniqueConstraint("bulletin_id", "version_no", name="uq_comm_bulletin_revision_version"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CommunicationBulletinRevision B{self.bulletin_id} V{self.version_no}>"


class CommunicationSurveyTemplate(TimestampMixin, db.Model):
    __tablename__ = "communication_survey_templates"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    survey_type = db.Column(db.String(50), nullable=False, default="kurum_ici", index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    created_by = db.relationship("User", foreign_keys=[created_by_user_id])
    updated_by = db.relationship("User", foreign_keys=[updated_by_user_id])

    questions = db.relationship(
        "CommunicationSurveyTemplateQuestion",
        back_populates="template",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="CommunicationSurveyTemplateQuestion.sort_order.asc()",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CommunicationSurveyTemplate {self.id} {self.title}>"


class CommunicationSurveyTemplateQuestion(TimestampMixin, db.Model):
    __tablename__ = "communication_survey_template_questions"

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(
        db.Integer,
        db.ForeignKey("communication_survey_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(30), nullable=False, default="single_choice", index=True)
    is_required = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=1, index=True)
    options_text = db.Column(db.Text, nullable=True)

    template = db.relationship("CommunicationSurveyTemplate", back_populates="questions")

    def parsed_options(self) -> list[str]:
        return [item.strip() for item in (self.options_text or "").splitlines() if item and item.strip()]

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CommunicationSurveyTemplateQuestion {self.id} T{self.template_id}>"