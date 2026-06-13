-- BYS360 Faz 8.1 Workflow Engine Hardening
-- Not: Uygulama route katmanı ensure_tables() ile aynı tabloları güvenli şekilde oluşturur.
-- Bu dosya BT/DBA ön kontrolü için opsiyonel referanstır.

CREATE TABLE IF NOT EXISTS workflow_instances(
    id SERIAL PRIMARY KEY,
    module VARCHAR(80) NOT NULL,
    entity_type VARCHAR(120),
    entity_id INTEGER,
    title VARCHAR(255) NOT NULL,
    subject_user_id INTEGER,
    period_id INTEGER,
    score NUMERIC(8,2),
    status VARCHAR(40) NOT NULL DEFAULT 'ACTIVE',
    current_step_name VARCHAR(255),
    priority VARCHAR(30) NOT NULL DEFAULT 'NORMAL',
    workflow_family VARCHAR(80) DEFAULT 'GENERAL',
    delayed_step_count INTEGER NOT NULL DEFAULT 0,
    created_by_id INTEGER,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    payload_json JSONB
);

CREATE TABLE IF NOT EXISTS workflow_steps(
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL REFERENCES workflow_instances(id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    step_code VARCHAR(80),
    step_type VARCHAR(40),
    step_name VARCHAR(255) NOT NULL,
    assigned_user_id INTEGER,
    visible_to_user_id INTEGER,
    status VARCHAR(40) NOT NULL DEFAULT 'PENDING',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_required BOOLEAN NOT NULL DEFAULT TRUE,
    started_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    due_at TIMESTAMP WITHOUT TIME ZONE,
    duration_minutes INTEGER,
    delay_state VARCHAR(30) NOT NULL DEFAULT 'NORMAL',
    delay_days NUMERIC(10,2) NOT NULL DEFAULT 0,
    escalation_level VARCHAR(30) NOT NULL DEFAULT 'NONE',
    last_reminded_at TIMESTAMP WITHOUT TIME ZONE,
    reminder_count INTEGER NOT NULL DEFAULT 0,
    notification_status VARCHAR(30) NOT NULL DEFAULT 'READY',
    note TEXT
);

CREATE TABLE IF NOT EXISTS workflow_logs(
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL REFERENCES workflow_instances(id) ON DELETE CASCADE,
    step_id INTEGER,
    user_id INTEGER,
    action VARCHAR(80) NOT NULL,
    old_status VARCHAR(40),
    new_status VARCHAR(40),
    note TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS performance_president_approvals(
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER NOT NULL UNIQUE,
    period_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    score NUMERIC(8,2) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'PENDING',
    workflow_id INTEGER REFERENCES workflow_instances(id) ON DELETE SET NULL,
    requested_by_id INTEGER,
    president_id INTEGER,
    decided_at TIMESTAMP WITHOUT TIME ZONE,
    decision_note TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workflow_notifications(
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL REFERENCES workflow_instances(id) ON DELETE CASCADE,
    step_id INTEGER REFERENCES workflow_steps(id) ON DELETE CASCADE,
    target_user_id INTEGER,
    notification_type VARCHAR(80) NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    status VARCHAR(40) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP WITHOUT TIME ZONE,
    payload_json JSONB
);

CREATE INDEX IF NOT EXISTS ix_workflow_instances_module_status ON workflow_instances(module,status);
CREATE INDEX IF NOT EXISTS ix_workflow_instances_subject_period ON workflow_instances(subject_user_id,period_id);
CREATE INDEX IF NOT EXISTS ix_workflow_steps_workflow_order ON workflow_steps(workflow_id,step_order);
CREATE INDEX IF NOT EXISTS ix_workflow_steps_status ON workflow_steps(status);
CREATE INDEX IF NOT EXISTS ix_perf_pres_approvals_status ON performance_president_approvals(status);
CREATE INDEX IF NOT EXISTS ix_workflow_notifications_status ON workflow_notifications(status);
CREATE INDEX IF NOT EXISTS ix_workflow_notifications_target ON workflow_notifications(target_user_id,status);
