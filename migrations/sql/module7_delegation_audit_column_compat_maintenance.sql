-- BYS360 delegation / audit column compatibility hotfix
-- Amaç:
-- 1) Var olan tabloları bozmadan eksik kolonları tamamlamak
-- 2) Farklı kolon adları kullanan eski şemalarla uyumluluk sağlamak
-- 3) Script'i tekrar çalıştırılabilir (idempotent) tutmak

BEGIN;

-- =========================================================
-- leave_records
-- =========================================================
CREATE TABLE IF NOT EXISTS leave_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'approved',
    leave_type VARCHAR(100),
    affects_performance BOOLEAN NOT NULL DEFAULT FALSE,
    performance_mode VARCHAR(30) NOT NULL DEFAULT 'informational',
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE leave_records
    ADD COLUMN IF NOT EXISTS affects_performance BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS performance_mode VARCHAR(30) NOT NULL DEFAULT 'informational',
    ADD COLUMN IF NOT EXISTS notes TEXT,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- =========================================================
-- delegation_assignments
-- =========================================================
CREATE TABLE IF NOT EXISTS delegation_assignments (
    id SERIAL PRIMARY KEY,
    source_user_id INTEGER,
    principal_user_id INTEGER,
    delegate_user_id INTEGER,
    manager_level INTEGER,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'approved',
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE delegation_assignments
    ADD COLUMN IF NOT EXISTS source_user_id INTEGER,
    ADD COLUMN IF NOT EXISTS principal_user_id INTEGER,
    ADD COLUMN IF NOT EXISTS delegate_user_id INTEGER,
    ADD COLUMN IF NOT EXISTS manager_level INTEGER,
    ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'approved',
    ADD COLUMN IF NOT EXISTS notes TEXT,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- Eski kolon adlarından veri taşı
DO $$
BEGIN
    -- user_id -> source/principal
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='delegation_assignments' AND column_name='user_id'
    ) THEN
        EXECUTE '
            UPDATE delegation_assignments
               SET source_user_id = COALESCE(source_user_id, user_id),
                   principal_user_id = COALESCE(principal_user_id, user_id)
             WHERE user_id IS NOT NULL
        ';
    END IF;

    -- owner_user_id -> source/principal
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='delegation_assignments' AND column_name='owner_user_id'
    ) THEN
        EXECUTE '
            UPDATE delegation_assignments
               SET source_user_id = COALESCE(source_user_id, owner_user_id),
                   principal_user_id = COALESCE(principal_user_id, owner_user_id)
             WHERE owner_user_id IS NOT NULL
        ';
    END IF;

    -- original_user_id -> source/principal
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='delegation_assignments' AND column_name='original_user_id'
    ) THEN
        EXECUTE '
            UPDATE delegation_assignments
               SET source_user_id = COALESCE(source_user_id, original_user_id),
                   principal_user_id = COALESCE(principal_user_id, original_user_id)
             WHERE original_user_id IS NOT NULL
        ';
    END IF;

    -- assignee_user_id -> delegate_user_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='delegation_assignments' AND column_name='assignee_user_id'
    ) THEN
        EXECUTE '
            UPDATE delegation_assignments
               SET delegate_user_id = COALESCE(delegate_user_id, assignee_user_id)
             WHERE assignee_user_id IS NOT NULL
        ';
    END IF;

    -- target_user_id -> delegate_user_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='delegation_assignments' AND column_name='target_user_id'
    ) THEN
        EXECUTE '
            UPDATE delegation_assignments
               SET delegate_user_id = COALESCE(delegate_user_id, target_user_id)
             WHERE target_user_id IS NOT NULL
        ';
    END IF;

    -- delegated_user_id -> delegate_user_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='delegation_assignments' AND column_name='delegated_user_id'
    ) THEN
        EXECUTE '
            UPDATE delegation_assignments
               SET delegate_user_id = COALESCE(delegate_user_id, delegated_user_id)
             WHERE delegated_user_id IS NOT NULL
        ';
    END IF;
END $$;

-- Boş kritik alanlar için makul fallback
UPDATE delegation_assignments
   SET principal_user_id = COALESCE(principal_user_id, source_user_id)
 WHERE principal_user_id IS NULL AND source_user_id IS NOT NULL;

UPDATE delegation_assignments
   SET source_user_id = COALESCE(source_user_id, principal_user_id)
 WHERE source_user_id IS NULL AND principal_user_id IS NOT NULL;

-- =========================================================
-- assignment_audit_logs
-- =========================================================
CREATE TABLE IF NOT EXISTS assignment_audit_logs (
    id SERIAL PRIMARY KEY,
    period_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    manager_level INTEGER NOT NULL,
    original_evaluator_id INTEGER,
    effective_evaluator_id INTEGER,
    resolution_type VARCHAR(100),
    message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE assignment_audit_logs
    ADD COLUMN IF NOT EXISTS period_id INTEGER,
    ADD COLUMN IF NOT EXISTS employee_id INTEGER,
    ADD COLUMN IF NOT EXISTS manager_level INTEGER,
    ADD COLUMN IF NOT EXISTS original_evaluator_id INTEGER,
    ADD COLUMN IF NOT EXISTS effective_evaluator_id INTEGER,
    ADD COLUMN IF NOT EXISTS resolution_type VARCHAR(100),
    ADD COLUMN IF NOT EXISTS message TEXT,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

DO $$
BEGIN
    -- evaluator_id -> original/effective fallback
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='assignment_audit_logs' AND column_name='evaluator_id'
    ) THEN
        EXECUTE '
            UPDATE assignment_audit_logs
               SET original_evaluator_id = COALESCE(original_evaluator_id, evaluator_id),
                   effective_evaluator_id = COALESCE(effective_evaluator_id, evaluator_id)
             WHERE evaluator_id IS NOT NULL
        ';
    END IF;

    -- assigned_evaluator_id -> effective_evaluator_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='assignment_audit_logs' AND column_name='assigned_evaluator_id'
    ) THEN
        EXECUTE '
            UPDATE assignment_audit_logs
               SET effective_evaluator_id = COALESCE(effective_evaluator_id, assigned_evaluator_id)
             WHERE assigned_evaluator_id IS NOT NULL
        ';
    END IF;
END $$;

-- =========================================================
-- Indexes
-- =========================================================
CREATE INDEX IF NOT EXISTS ix_leave_records_user_dates
    ON leave_records (user_id, start_date, end_date);

CREATE INDEX IF NOT EXISTS ix_delegation_assignments_source_dates
    ON delegation_assignments (source_user_id, manager_level, start_date, end_date);

CREATE INDEX IF NOT EXISTS ix_delegation_assignments_delegate_dates
    ON delegation_assignments (delegate_user_id, manager_level, start_date, end_date);

CREATE INDEX IF NOT EXISTS ix_assignment_audit_logs_period_employee
    ON assignment_audit_logs (period_id, employee_id, manager_level);

COMMIT;
