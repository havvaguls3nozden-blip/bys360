-- BYS360 Efektif Amir Zinciri için örnek destek tabloları

CREATE TABLE IF NOT EXISTS leave_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'approved',
    leave_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS delegation_assignments (
    id SERIAL PRIMARY KEY,
    source_user_id INTEGER NOT NULL,
    delegate_user_id INTEGER NOT NULL,
    manager_level INTEGER,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'approved',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assignment_audit_logs (
    id SERIAL PRIMARY KEY,
    period_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    manager_level INTEGER NOT NULL,
    original_evaluator_id INTEGER,
    effective_evaluator_id INTEGER,
    resolution_type VARCHAR(100),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_leave_records_user_dates
    ON leave_records (user_id, start_date, end_date);

CREATE INDEX IF NOT EXISTS ix_delegation_assignments_source_dates
    ON delegation_assignments (source_user_id, manager_level, start_date, end_date);

CREATE INDEX IF NOT EXISTS ix_assignment_audit_logs_period_employee
    ON assignment_audit_logs (period_id, employee_id, manager_level);
