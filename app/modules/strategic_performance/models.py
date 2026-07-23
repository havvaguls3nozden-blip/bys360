"""BYS360 SP-1A stratejik performans veri modelleri.

Bu dosya mevcut projeye güvenli ek katman olarak tasarlanmıştır.
Mevcut performans tablolarını değiştirmez.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from app.extensions import db
except Exception:  # Bazı BYS360 sürümlerinde db app içinden gelebilir.
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    from app import db


class PerformanceTargetPeriod(db.Model):
    __tablename__ = "performance_target_periods"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    period_type = db.Column(db.String(50), nullable=False, default="yearly")
    scope_type = db.Column(db.String(50), nullable=False, default="institution")
    status = db.Column(db.String(50), nullable=False, default="active")
    created_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class PerformanceTarget(db.Model):
    __tablename__ = "performance_targets"

    id = db.Column(db.Integer, primary_key=True)
    target_code = db.Column(db.String(50), unique=True, nullable=False)
    target_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    target_type = db.Column(db.String(50), nullable=False, default="personnel")
    category = db.Column(db.String(100))
    owner_user_id = db.Column(db.Integer)
    owner_unit_id = db.Column(db.Integer)
    weight = db.Column(db.Numeric(5, 2), default=0)
    target_value = db.Column(db.Numeric(12, 2))
    current_value = db.Column(db.Numeric(12, 2))
    completion_rate = db.Column(db.Numeric(5, 2))
    status = db.Column(db.String(50), nullable=False, default="ongoing")
    risk_level = db.Column(db.String(50), nullable=False, default="low")
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    period_id = db.Column(db.Integer, db.ForeignKey("performance_target_periods.id"))
    created_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompetencyLibrary(db.Model):
    __tablename__ = "competency_library"

    id = db.Column(db.Integer, primary_key=True)
    competency_name = db.Column(db.String(255), nullable=False, unique=True)
    competency_category = db.Column(db.String(100))
    description = db.Column(db.Text)
    minimum_level = db.Column(db.Integer, default=1)
    default_weight = db.Column(db.Numeric(5, 2), default=0)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class RoleCompetencyTemplate(db.Model):
    __tablename__ = "role_competency_templates"

    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(255), nullable=False)
    competency_id = db.Column(db.Integer, db.ForeignKey("competency_library.id"), nullable=False)
    weight = db.Column(db.Numeric(5, 2), default=0)
    required_level = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class SelfReview(db.Model):
    __tablename__ = "self_reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    performance_period_id = db.Column(db.Integer)
    summary = db.Column(db.Text)
    achievements = db.Column(db.Text)
    difficulties = db.Column(db.Text)
    development_needs = db.Column(db.Text)
    manager_visible = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
