-- BYS360 Egitim Faz 15 | Kariyer planlama operasyon tablolari
-- PostgreSQL icin hazirlanmistir.

CREATE TABLE IF NOT EXISTS education_career_plans (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mentor_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    target_unit_id INTEGER NULL REFERENCES organization_units(id) ON DELETE SET NULL,
    current_role VARCHAR(150) NULL,
    target_role VARCHAR(150) NOT NULL,
    readiness_level VARCHAR(40) NOT NULL DEFAULT 'gelisimde',
    development_priority VARCHAR(40) NOT NULL DEFAULT 'orta',
    status VARCHAR(40) NOT NULL DEFAULT 'taslak',
    target_date DATE NULL,
    succession_candidate BOOLEAN NOT NULL DEFAULT FALSE,
    development_focus VARCHAR(255) NULL,
    development_actions TEXT NULL,
    recommended_trainings TEXT NULL,
    manager_note TEXT NULL,
    latest_review_note TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_education_career_employee_status ON education_career_plans(employee_id, status);
CREATE INDEX IF NOT EXISTS ix_education_career_priority_readiness ON education_career_plans(development_priority, readiness_level);
CREATE INDEX IF NOT EXISTS ix_education_career_target_date ON education_career_plans(target_date);
