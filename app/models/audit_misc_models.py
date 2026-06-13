"""Audit ve misc model alani icin ayrilmis gecis dosyasi."""

from .base import TimestampMixin, db


class AuditLog(TimestampMixin, db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    entity_type = db.Column(db.String(100), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    old_data_json = db.Column(db.Text, nullable=True)
    new_data_json = db.Column(db.Text, nullable=True)
    summary = db.Column(db.String(255), nullable=True)
    endpoint = db.Column(db.String(255), nullable=True, index=True)
    ip_address = db.Column(db.String(64), nullable=True)

    user = db.relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<AuditLog id={self.id} action={self.action} entity={self.entity_type}:{self.entity_id}>"


class PerformanceEvaluationHistory(TimestampMixin, db.Model):
    __tablename__ = "performance_evaluation_history"

    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey("performance_evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_level = db.Column(db.Integer, nullable=True, index=True)
    action_type = db.Column(db.String(50), nullable=False, index=True)
    from_status = db.Column(db.String(50), nullable=True, index=True)
    to_status = db.Column(db.String(50), nullable=True, index=True)
    note = db.Column(db.Text, nullable=True)
    score_snapshot = db.Column(db.JSON, nullable=True)

    evaluation = db.relationship("PerformanceEvaluation", foreign_keys=[evaluation_id])
    actor = db.relationship("User", foreign_keys=[actor_user_id])

    def __repr__(self):
        return f"<PerformanceEvaluationHistory eval={self.evaluation_id} action={self.action_type} level={self.actor_level}>"


__all__ = ["TimestampMixin", "db", "AuditLog", "PerformanceEvaluationHistory"]