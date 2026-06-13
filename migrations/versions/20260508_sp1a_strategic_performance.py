"""BYS360 SP-1A strategic performance tables

Revision ID: 20260508_sp1a
Revises: 
Create Date: 2026-05-08
"""
from alembic import op
import sqlalchemy as sa

revision = "20260508_sp1a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE IF NOT EXISTS performance_target_periods (id SERIAL PRIMARY KEY, name VARCHAR(255) NOT NULL, description TEXT, start_date DATE NOT NULL, end_date DATE NOT NULL, period_type VARCHAR(50) NOT NULL DEFAULT 'yearly', scope_type VARCHAR(50) NOT NULL DEFAULT 'institution', status VARCHAR(50) NOT NULL DEFAULT 'active', created_by INTEGER, created_at TIMESTAMP DEFAULT NOW() NOT NULL)")
    op.execute("CREATE TABLE IF NOT EXISTS performance_targets (id SERIAL PRIMARY KEY, target_code VARCHAR(50) UNIQUE NOT NULL, target_name VARCHAR(255) NOT NULL, description TEXT, target_type VARCHAR(50) NOT NULL DEFAULT 'personnel', category VARCHAR(100), owner_user_id INTEGER, owner_unit_id INTEGER, weight NUMERIC(5,2) DEFAULT 0, target_value NUMERIC(12,2), current_value NUMERIC(12,2), completion_rate NUMERIC(5,2), status VARCHAR(50) NOT NULL DEFAULT 'ongoing', risk_level VARCHAR(50) NOT NULL DEFAULT 'low', start_date DATE, end_date DATE, period_id INTEGER REFERENCES performance_target_periods(id), created_by INTEGER, created_at TIMESTAMP DEFAULT NOW() NOT NULL, updated_at TIMESTAMP DEFAULT NOW())")
    op.execute("CREATE TABLE IF NOT EXISTS competency_library (id SERIAL PRIMARY KEY, competency_name VARCHAR(255) UNIQUE NOT NULL, competency_category VARCHAR(100), description TEXT, minimum_level INTEGER DEFAULT 1, default_weight NUMERIC(5,2) DEFAULT 0, active BOOLEAN DEFAULT TRUE NOT NULL, created_at TIMESTAMP DEFAULT NOW() NOT NULL)")
    op.execute("CREATE TABLE IF NOT EXISTS role_competency_templates (id SERIAL PRIMARY KEY, role_name VARCHAR(255) NOT NULL, competency_id INTEGER NOT NULL REFERENCES competency_library(id), weight NUMERIC(5,2) DEFAULT 0, required_level INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT NOW() NOT NULL)")
    op.execute("CREATE TABLE IF NOT EXISTS self_reviews (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL, performance_period_id INTEGER, summary TEXT, achievements TEXT, difficulties TEXT, development_needs TEXT, manager_visible BOOLEAN DEFAULT TRUE NOT NULL, created_at TIMESTAMP DEFAULT NOW() NOT NULL, updated_at TIMESTAMP DEFAULT NOW())")
    op.execute("CREATE INDEX IF NOT EXISTS ix_performance_targets_owner_user ON performance_targets(owner_user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_performance_targets_owner_unit ON performance_targets(owner_unit_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_performance_targets_period ON performance_targets(period_id)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS self_reviews")
    op.execute("DROP TABLE IF EXISTS role_competency_templates")
    op.execute("DROP TABLE IF EXISTS competency_library")
    op.execute("DROP TABLE IF EXISTS performance_targets")
    op.execute("DROP TABLE IF EXISTS performance_target_periods")
