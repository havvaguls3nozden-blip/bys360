
"""BYS360 schema guard - ALTER TABLE patch tanımları.

performance_evaluations, performance_periods ve evaluation_assignments
tablolarına eklenen delta değişiklikleri.
"""
from __future__ import annotations

SCHEMA_PATCHES: tuple[tuple[str, str], ...] = (
    ("workflow_status", "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS workflow_status VARCHAR(50) NOT NULL DEFAULT 'taslak_1_amir'"),
    ("level_1_submitted_to_level_2_at", "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS level_1_submitted_to_level_2_at TIMESTAMP NULL"),
    ("level_2_seen_level_1_at", "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS level_2_seen_level_1_at TIMESTAMP NULL"),
    ("level_2_returned_to_level_1_at", "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS level_2_returned_to_level_1_at TIMESTAMP NULL"),
    ("level_2_return_note", "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS level_2_return_note TEXT NULL"),
    ("level_2_returned_by_id", "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS level_2_returned_by_id INTEGER NULL"),
    ("level_1_last_resubmitted_at", "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS level_1_last_resubmitted_at TIMESTAMP NULL"),
    ("employee_score_viewed_at", "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS employee_score_viewed_at TIMESTAMP NULL"),
    ("employee_score_acknowledged_at", "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS employee_score_acknowledged_at TIMESTAMP NULL"),
    ("employee_score_acknowledged_note", "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS employee_score_acknowledged_note TEXT NULL"),
    ("minimum_presence_days_for_evaluation", "ALTER TABLE performance_periods ADD COLUMN IF NOT EXISTS minimum_presence_days_for_evaluation DOUBLE PRECISION NOT NULL DEFAULT 0"),
    ("leave_skip_threshold_days", "ALTER TABLE performance_periods ADD COLUMN IF NOT EXISTS leave_skip_threshold_days DOUBLE PRECISION NULL"),
    ("absence_skip_threshold_days", "ALTER TABLE performance_periods ADD COLUMN IF NOT EXISTS absence_skip_threshold_days DOUBLE PRECISION NULL"),
    ("auto_skip_if_fully_absent", "ALTER TABLE performance_periods ADD COLUMN IF NOT EXISTS auto_skip_if_fully_absent BOOLEAN NOT NULL DEFAULT TRUE"),
    ("manager_delegation_required", "ALTER TABLE performance_periods ADD COLUMN IF NOT EXISTS manager_delegation_required BOOLEAN NOT NULL DEFAULT TRUE"),
    ("evaluation_start_date", "ALTER TABLE performance_periods ADD COLUMN IF NOT EXISTS evaluation_start_date DATE NULL"),
    ("evaluation_end_date", "ALTER TABLE performance_periods ADD COLUMN IF NOT EXISTS evaluation_end_date DATE NULL"),
    ("evaluation_due_days", "ALTER TABLE performance_periods ADD COLUMN IF NOT EXISTS evaluation_due_days INTEGER NULL"),
    ("evaluation_exempted", "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS evaluation_exempted BOOLEAN NOT NULL DEFAULT FALSE"),
    ("evaluation_exemption_reason", "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS evaluation_exemption_reason VARCHAR(255) NULL"),
    ("employee_leave_days_in_period", "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS employee_leave_days_in_period DOUBLE PRECISION NOT NULL DEFAULT 0"),
    ("employee_absence_days_in_period", "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS employee_absence_days_in_period DOUBLE PRECISION NOT NULL DEFAULT 0"),
    ("employee_available_days_in_period", "ALTER TABLE performance_evaluations ADD COLUMN IF NOT EXISTS employee_available_days_in_period DOUBLE PRECISION NOT NULL DEFAULT 0"),
    ("original_evaluator_id", "ALTER TABLE evaluation_assignments ADD COLUMN IF NOT EXISTS original_evaluator_id INTEGER NULL"),
    ("delegation_id", "ALTER TABLE evaluation_assignments ADD COLUMN IF NOT EXISTS delegation_id INTEGER NULL"),
    ("assignment_source", "ALTER TABLE evaluation_assignments ADD COLUMN IF NOT EXISTS assignment_source VARCHAR(30) NOT NULL DEFAULT 'standard'"),
    ("coverage_note", "ALTER TABLE evaluation_assignments ADD COLUMN IF NOT EXISTS coverage_note VARCHAR(255) NULL"),
    ("due_date", "ALTER TABLE evaluation_assignments ADD COLUMN IF NOT EXISTS due_date TIMESTAMP NULL"),
    ("ix_evaluation_assignments_due_date", "CREATE INDEX IF NOT EXISTS ix_evaluation_assignments_due_date ON evaluation_assignments (due_date)"),
    ("ix_performance_evaluations_workflow_status", "CREATE INDEX IF NOT EXISTS ix_performance_evaluations_workflow_status ON performance_evaluations (workflow_status)"),
    ("ix_performance_evaluations_evaluation_exempted", "CREATE INDEX IF NOT EXISTS ix_performance_evaluations_evaluation_exempted ON performance_evaluations (evaluation_exempted)"),
    # BYS360 Faz 2 — Personel kategori ve grup altyapısı.
    ("phase2_personnel_categories_table", """
        CREATE TABLE IF NOT EXISTS personnel_categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(80) NOT NULL UNIQUE,
            code VARCHAR(80) NOT NULL UNIQUE,
            description VARCHAR(255) NULL,
            sort_order INTEGER NOT NULL DEFAULT 100,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """),
    ("phase2_users_personnel_category", "ALTER TABLE users ADD COLUMN IF NOT EXISTS personnel_category VARCHAR(80) NULL DEFAULT 'Diğer'"),
    ("phase2_users_performance_category_id", "ALTER TABLE users ADD COLUMN IF NOT EXISTS performance_category_id INTEGER NULL"),
    ("phase2_ix_users_personnel_category", "CREATE INDEX IF NOT EXISTS ix_users_personnel_category ON users (personnel_category)"),
    ("phase2_ix_users_performance_category_id", "CREATE INDEX IF NOT EXISTS ix_users_performance_category_id ON users (performance_category_id)"),
    ("phase2_ix_personnel_categories_name", "CREATE INDEX IF NOT EXISTS ix_personnel_categories_name ON personnel_categories (name)"),
    ("phase2_ix_personnel_categories_code", "CREATE INDEX IF NOT EXISTS ix_personnel_categories_code ON personnel_categories (code)"),
    ("phase2_ix_personnel_categories_active_sort", "CREATE INDEX IF NOT EXISTS ix_personnel_categories_active_sort ON personnel_categories (is_active, sort_order)"),
    ("phase2_seed_category_guvenlik", """
        INSERT INTO personnel_categories (code, name, description, sort_order, is_active)
        SELECT 'guvenlik', 'Güvenlik', 'Güvenlik personel performans kategori grubu', 10, TRUE
        WHERE NOT EXISTS (SELECT 1 FROM personnel_categories WHERE code = 'guvenlik' OR name = 'Güvenlik')
    """),
    ("phase2_seed_category_temizlik", """
        INSERT INTO personnel_categories (code, name, description, sort_order, is_active)
        SELECT 'temizlik', 'Temizlik', 'Temizlik personel performans kategori grubu', 20, TRUE
        WHERE NOT EXISTS (SELECT 1 FROM personnel_categories WHERE code = 'temizlik' OR name = 'Temizlik')
    """),
    ("phase2_seed_category_idari", """
        INSERT INTO personnel_categories (code, name, description, sort_order, is_active)
        SELECT 'idari_personel', 'İdari Personel', 'İdari Personel performans kategori grubu', 30, TRUE
        WHERE NOT EXISTS (SELECT 1 FROM personnel_categories WHERE code = 'idari_personel' OR name = 'İdari Personel')
    """),
    ("phase2_seed_category_teknik", """
        INSERT INTO personnel_categories (code, name, description, sort_order, is_active)
        SELECT 'teknik_personel', 'Teknik Personel', 'Teknik Personel performans kategori grubu', 40, TRUE
        WHERE NOT EXISTS (SELECT 1 FROM personnel_categories WHERE code = 'teknik_personel' OR name = 'Teknik Personel')
    """),
    ("phase2_seed_category_deneme", """
        INSERT INTO personnel_categories (code, name, description, sort_order, is_active)
        SELECT 'deneme_sureli_personel', 'Deneme Süreli Personel', 'Deneme Süreli Personel performans kategori grubu', 50, TRUE
        WHERE NOT EXISTS (SELECT 1 FROM personnel_categories WHERE code = 'deneme_sureli_personel' OR name = 'Deneme Süreli Personel')
    """),
    ("phase2_seed_category_diger", """
        INSERT INTO personnel_categories (code, name, description, sort_order, is_active)
        SELECT 'diger', 'Diğer', 'Diğer personel performans kategori grubu', 60, TRUE
        WHERE NOT EXISTS (SELECT 1 FROM personnel_categories WHERE code = 'diger' OR name = 'Diğer')
    """),
    ("phase2_backfill_users_personnel_category", "UPDATE users SET personnel_category = 'Diğer' WHERE personnel_category IS NULL OR TRIM(personnel_category) = ''"),
    ("phase2_backfill_users_performance_category_id", """
        UPDATE users
           SET performance_category_id = pc.id
          FROM personnel_categories pc
         WHERE users.performance_category_id IS NULL
           AND users.personnel_category = pc.name
    """),
)
