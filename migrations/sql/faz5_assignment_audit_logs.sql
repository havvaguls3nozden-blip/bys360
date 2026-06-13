
-- Faz 5: Assignment audit log tablosu
CREATE TABLE IF NOT EXISTS assignment_audit_logs (
    id SERIAL PRIMARY KEY,
    period_id INTEGER NULL REFERENCES performance_periods(id) ON DELETE SET NULL,
    employee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    manager_level INTEGER NOT NULL,
    original_evaluator_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    effective_evaluator_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    reason_type VARCHAR(50) NOT NULL,
    details_json TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_assignment_audit_logs_period_id ON assignment_audit_logs(period_id);
CREATE INDEX IF NOT EXISTS ix_assignment_audit_logs_employee_id ON assignment_audit_logs(employee_id);
CREATE INDEX IF NOT EXISTS ix_assignment_audit_logs_manager_level ON assignment_audit_logs(manager_level);
CREATE INDEX IF NOT EXISTS ix_assignment_audit_logs_reason_type ON assignment_audit_logs(reason_type);
