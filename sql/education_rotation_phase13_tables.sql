-- BYS360 Egitim Faz 13 | Rotasyon onay ve belge akisi
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

ALTER TABLE education_rotation_assignments ADD COLUMN IF NOT EXISTS source_approval_status VARCHAR(30) NOT NULL DEFAULT 'beklemede';
ALTER TABLE education_rotation_assignments ADD COLUMN IF NOT EXISTS source_approval_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE education_rotation_assignments ADD COLUMN IF NOT EXISTS source_approval_note TEXT NULL;
ALTER TABLE education_rotation_assignments ADD COLUMN IF NOT EXISTS source_approved_at TIMESTAMP WITHOUT TIME ZONE NULL;

ALTER TABLE education_rotation_assignments ADD COLUMN IF NOT EXISTS target_approval_status VARCHAR(30) NOT NULL DEFAULT 'beklemede';
ALTER TABLE education_rotation_assignments ADD COLUMN IF NOT EXISTS target_approval_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE education_rotation_assignments ADD COLUMN IF NOT EXISTS target_approval_note TEXT NULL;
ALTER TABLE education_rotation_assignments ADD COLUMN IF NOT EXISTS target_approved_at TIMESTAMP WITHOUT TIME ZONE NULL;

CREATE INDEX IF NOT EXISTS ix_rotation_employee_status ON education_rotation_assignments (employee_id, status);
CREATE INDEX IF NOT EXISTS ix_rotation_source_target ON education_rotation_assignments (source_unit_id, target_unit_id);
CREATE INDEX IF NOT EXISTS ix_rotation_start_date ON education_rotation_assignments (start_date);
CREATE INDEX IF NOT EXISTS ix_rotation_end_date ON education_rotation_assignments (end_date);
CREATE INDEX IF NOT EXISTS ix_rotation_source_approval_status ON education_rotation_assignments (source_approval_status);
CREATE INDEX IF NOT EXISTS ix_rotation_target_approval_status ON education_rotation_assignments (target_approval_status);

CREATE TABLE IF NOT EXISTS education_rotation_documents (
    id SERIAL PRIMARY KEY,
    rotation_id INTEGER NOT NULL REFERENCES education_rotation_assignments(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) NOT NULL DEFAULT 'genel',
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL UNIQUE,
    storage_path VARCHAR(500) NOT NULL,
    mime_type VARCHAR(150) NULL,
    file_size BIGINT NOT NULL DEFAULT 0,
    notes TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_rotation_document_rotation_type ON education_rotation_documents (rotation_id, document_type);
