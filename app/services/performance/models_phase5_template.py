
"""
Faz 5 için önerilen çekirdek modeller.
Bu dosya doğrudan import edilmek zorunda değildir;
mevcut model yapınıza kontrollü taşıma için referans şablon olarak bırakılmıştır.
"""

from app.core.datetime_utils import utc_now
from datetime import datetime
from app.extensions import db


class LeaveRecord(db.Model):
    __tablename__ = "leave_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    leave_type = db.Column(db.String(50), nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="approved", index=True)
    affects_performance = db.Column(db.Boolean, default=False, nullable=False)
    performance_mode = db.Column(db.String(30), nullable=False, default="informational")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class DelegationAssignment(db.Model):
    __tablename__ = "delegation_assignments"

    id = db.Column(db.Integer, primary_key=True)
    principal_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    delegate_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    manager_level = db.Column(db.Integer, nullable=False, default=0, index=True)  # 0 = all levels
    scope_type = db.Column(db.String(50), nullable=False, default="performance")
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=True, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class AssignmentAuditLog(db.Model):
    __tablename__ = "assignment_audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey("performance_periods.id"), nullable=True, index=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    manager_level = db.Column(db.Integer, nullable=False, index=True)
    original_evaluator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    effective_evaluator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    reason_type = db.Column(db.String(50), nullable=False, index=True)  # normal, delegated, excluded_due_leave
    details_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)