"""add ai support tables

Revision ID: b7f4e2a1c9d0
Revises: 71d0eccf02c0
Create Date: 2026-04-03 12:40:00
"""

from alembic import op

revision = 'b7f4e2a1c9d0'
down_revision = '71d0eccf02c0'
branch_labels = None
depends_on = None


def upgrade():
    statements = [
        """
        CREATE TABLE IF NOT EXISTS ai_request_logs (
            id SERIAL PRIMARY KEY,
            module_type VARCHAR(50) NOT NULL,
            feature_type VARCHAR(50) NOT NULL,
            target_table VARCHAR(100) NULL,
            target_id INTEGER NULL,
            user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
            request_text TEXT NULL,
            response_text TEXT NULL,
            provider_name VARCHAR(100) NULL,
            model_name VARCHAR(100) NULL,
            prompt_version VARCHAR(50) NULL,
            status VARCHAR(30) NOT NULL DEFAULT 'completed',
            latency_ms INTEGER NULL,
            token_in INTEGER NULL,
            token_out INTEGER NULL,
            was_masked BOOLEAN NOT NULL DEFAULT TRUE,
            was_user_visible BOOLEAN NOT NULL DEFAULT TRUE,
            error_message TEXT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_ai_request_logs_module_type ON ai_request_logs(module_type)",
        "CREATE INDEX IF NOT EXISTS ix_ai_request_logs_feature_type ON ai_request_logs(feature_type)",
        "CREATE INDEX IF NOT EXISTS ix_ai_request_logs_target_table ON ai_request_logs(target_table)",
        "CREATE INDEX IF NOT EXISTS ix_ai_request_logs_target_id ON ai_request_logs(target_id)",
        "CREATE INDEX IF NOT EXISTS ix_ai_request_logs_user_id ON ai_request_logs(user_id)",
        "CREATE INDEX IF NOT EXISTS ix_ai_request_logs_status ON ai_request_logs(status)",
        "CREATE INDEX IF NOT EXISTS ix_ai_request_logs_module_target ON ai_request_logs(module_type, target_table, target_id)",
        """
        CREATE TABLE IF NOT EXISTS ai_recommendations (
            id SERIAL PRIMARY KEY,
            module_type VARCHAR(50) NOT NULL,
            target_table VARCHAR(100) NOT NULL,
            target_id INTEGER NOT NULL,
            recommendation_type VARCHAR(50) NOT NULL,
            title VARCHAR(255) NOT NULL,
            body TEXT NULL,
            severity VARCHAR(20) NULL DEFAULT 'info',
            status VARCHAR(30) NOT NULL DEFAULT 'open',
            ai_request_log_id INTEGER NULL REFERENCES ai_request_logs(id) ON DELETE SET NULL,
            reviewed_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
            reviewed_at TIMESTAMP NULL,
            created_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
            updated_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_ai_recommendations_module_type ON ai_recommendations(module_type)",
        "CREATE INDEX IF NOT EXISTS ix_ai_recommendations_target_table ON ai_recommendations(target_table)",
        "CREATE INDEX IF NOT EXISTS ix_ai_recommendations_target_id ON ai_recommendations(target_id)",
        "CREATE INDEX IF NOT EXISTS ix_ai_recommendations_recommendation_type ON ai_recommendations(recommendation_type)",
        "CREATE INDEX IF NOT EXISTS ix_ai_recommendations_severity ON ai_recommendations(severity)",
        "CREATE INDEX IF NOT EXISTS ix_ai_recommendations_status ON ai_recommendations(status)",
        "CREATE INDEX IF NOT EXISTS ix_ai_recommendations_ai_request_log_id ON ai_recommendations(ai_request_log_id)",
        "CREATE INDEX IF NOT EXISTS ix_ai_recommendations_reviewed_by_user_id ON ai_recommendations(reviewed_by_user_id)",
        "CREATE INDEX IF NOT EXISTS ix_ai_recommendations_created_by_id ON ai_recommendations(created_by_id)",
        "CREATE INDEX IF NOT EXISTS ix_ai_recommendations_updated_by_id ON ai_recommendations(updated_by_id)",
        "CREATE INDEX IF NOT EXISTS ix_ai_recommendations_target ON ai_recommendations(module_type, target_table, target_id)",
        """
        CREATE TABLE IF NOT EXISTS ai_feedback_logs (
            id SERIAL PRIMARY KEY,
            ai_request_log_id INTEGER NOT NULL REFERENCES ai_request_logs(id) ON DELETE CASCADE,
            user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
            feedback_type VARCHAR(30) NOT NULL,
            feedback_note TEXT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_ai_feedback_logs_ai_request_log_id ON ai_feedback_logs(ai_request_log_id)",
        "CREATE INDEX IF NOT EXISTS ix_ai_feedback_logs_user_id ON ai_feedback_logs(user_id)",
        "CREATE INDEX IF NOT EXISTS ix_ai_feedback_logs_feedback_type ON ai_feedback_logs(feedback_type)",
        """
        CREATE TABLE IF NOT EXISTS ai_redaction_rules (
            id SERIAL PRIMARY KEY,
            module_type VARCHAR(50) NOT NULL,
            field_name VARCHAR(100) NOT NULL,
            redaction_type VARCHAR(50) NOT NULL,
            replacement_text VARCHAR(100) NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
            updated_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_ai_redaction_rules_module_field UNIQUE (module_type, field_name)
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_ai_redaction_rules_module_type ON ai_redaction_rules(module_type)",
        "CREATE INDEX IF NOT EXISTS ix_ai_redaction_rules_field_name ON ai_redaction_rules(field_name)",
        "CREATE INDEX IF NOT EXISTS ix_ai_redaction_rules_is_active ON ai_redaction_rules(is_active)",
        """
        CREATE TABLE IF NOT EXISTS ai_summary_cache (
            id SERIAL PRIMARY KEY,
            module_type VARCHAR(50) NOT NULL,
            target_table VARCHAR(100) NOT NULL,
            target_id INTEGER NOT NULL,
            summary_kind VARCHAR(50) NOT NULL,
            summary_text TEXT NOT NULL,
            source_hash VARCHAR(128) NULL,
            expires_at TIMESTAMP NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_ai_summary_cache_target_kind UNIQUE (module_type, target_table, target_id, summary_kind)
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_ai_summary_cache_module_type ON ai_summary_cache(module_type)",
        "CREATE INDEX IF NOT EXISTS ix_ai_summary_cache_target_table ON ai_summary_cache(target_table)",
        "CREATE INDEX IF NOT EXISTS ix_ai_summary_cache_target_id ON ai_summary_cache(target_id)",
        "CREATE INDEX IF NOT EXISTS ix_ai_summary_cache_summary_kind ON ai_summary_cache(summary_kind)",
        "CREATE INDEX IF NOT EXISTS ix_ai_summary_cache_source_hash ON ai_summary_cache(source_hash)",
        "CREATE INDEX IF NOT EXISTS ix_ai_summary_cache_expires_at ON ai_summary_cache(expires_at)",
    ]
    for stmt in statements:
        op.execute(stmt)


def downgrade():
    for stmt in [
        "DROP TABLE IF EXISTS ai_summary_cache",
        "DROP TABLE IF EXISTS ai_redaction_rules",
        "DROP TABLE IF EXISTS ai_feedback_logs",
        "DROP TABLE IF EXISTS ai_recommendations",
        "DROP TABLE IF EXISTS ai_request_logs",
    ]:
        op.execute(stmt)
