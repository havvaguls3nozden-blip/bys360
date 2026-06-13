
-- Faz 5: Leave ve delegation çekirdek tabloları
CREATE TABLE IF NOT EXISTS leave_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    leave_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'approved',
    affects_performance BOOLEAN NOT NULL DEFAULT FALSE,
    performance_mode VARCHAR(30) NOT NULL DEFAULT 'informational',
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_leave_records_user_id ON leave_records(user_id);
CREATE INDEX IF NOT EXISTS ix_leave_records_start_date ON leave_records(start_date);
CREATE INDEX IF NOT EXISTS ix_leave_records_end_date ON leave_records(end_date);
CREATE INDEX IF NOT EXISTS ix_leave_records_status ON leave_records(status);

CREATE TABLE IF NOT EXISTS delegation_assignments (
    id SERIAL PRIMARY KEY,
    principal_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    delegate_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    manager_level INTEGER NOT NULL DEFAULT 0,
    scope_type VARCHAR(50) NOT NULL DEFAULT 'performance',
    start_date DATE NOT NULL,
    end_date DATE NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_delegation_assignments_principal_user_id ON delegation_assignments(principal_user_id);
CREATE INDEX IF NOT EXISTS ix_delegation_assignments_delegate_user_id ON delegation_assignments(delegate_user_id);
CREATE INDEX IF NOT EXISTS ix_delegation_assignments_manager_level ON delegation_assignments(manager_level);
CREATE INDEX IF NOT EXISTS ix_delegation_assignments_scope_type ON delegation_assignments(scope_type);
