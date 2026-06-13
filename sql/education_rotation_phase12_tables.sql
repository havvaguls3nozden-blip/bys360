-- BYS360 Egitim Faz 12 | Rotasyon operasyon tablosu
-- PostgreSQL icin hazirlanmistir.

CREATE TABLE IF NOT EXISTS education_rotation_assignments (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_unit_id INTEGER NULL REFERENCES organization_units(id) ON DELETE SET NULL,
    target_unit_id INTEGER NULL REFERENCES organization_units(id) ON DELETE SET NULL,
    mentor_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    requested_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    approved_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    rotation_reason VARCHAR(50) NOT NULL DEFAULT 'kurumsal_ihtiyac',
    status VARCHAR(40) NOT NULL DEFAULT 'taslak',
    approval_status VARCHAR(30) NOT NULL DEFAULT 'beklemede',
    objective TEXT NULL,
    handover_note TEXT NULL,
    interim_review_date DATE NULL,
    interim_review_note TEXT NULL,
    closure_note TEXT NULL,
    recommendation_note TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_rotation_employee_status ON education_rotation_assignments (employee_id, status);
CREATE INDEX IF NOT EXISTS ix_rotation_source_target ON education_rotation_assignments (source_unit_id, target_unit_id);
CREATE INDEX IF NOT EXISTS ix_rotation_start_date ON education_rotation_assignments (start_date);
CREATE INDEX IF NOT EXISTS ix_rotation_end_date ON education_rotation_assignments (end_date);
