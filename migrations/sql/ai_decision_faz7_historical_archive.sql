-- BYS360_AI_DECISION_FAZ7_HISTORICAL_ARCHIVE_SQL_OK
-- Geçmiş yıl karne ve puan arşivi için karar destek şema/seed uyumu.

CREATE TABLE IF NOT EXISTS performance_archived_results (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    personnel_id INTEGER,
    registry_no VARCHAR(60),
    personnel_name VARCHAR(255),
    period_year INTEGER,
    period_title VARCHAR(180),
    score_value NUMERIC(10,2),
    score_label VARCHAR(120),
    general_comment TEXT,
    source_document VARCHAR(255),
    visibility_status VARCHAR(40) DEFAULT 'active',
    created_by_id INTEGER,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

ALTER TABLE performance_archived_results ADD COLUMN IF NOT EXISTS user_id INTEGER;
ALTER TABLE performance_archived_results ADD COLUMN IF NOT EXISTS personnel_id INTEGER;
ALTER TABLE performance_archived_results ADD COLUMN IF NOT EXISTS registry_no VARCHAR(60);
ALTER TABLE performance_archived_results ADD COLUMN IF NOT EXISTS personnel_name VARCHAR(255);
ALTER TABLE performance_archived_results ADD COLUMN IF NOT EXISTS period_year INTEGER;
ALTER TABLE performance_archived_results ADD COLUMN IF NOT EXISTS period_title VARCHAR(180);
ALTER TABLE performance_archived_results ADD COLUMN IF NOT EXISTS score_value NUMERIC(10,2);
ALTER TABLE performance_archived_results ADD COLUMN IF NOT EXISTS score_label VARCHAR(120);
ALTER TABLE performance_archived_results ADD COLUMN IF NOT EXISTS general_comment TEXT;
ALTER TABLE performance_archived_results ADD COLUMN IF NOT EXISTS source_document VARCHAR(255);
ALTER TABLE performance_archived_results ADD COLUMN IF NOT EXISTS visibility_status VARCHAR(40) DEFAULT 'active';
ALTER TABLE performance_archived_results ADD COLUMN IF NOT EXISTS created_by_id INTEGER;
ALTER TABLE performance_archived_results ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW();
ALTER TABLE performance_archived_results ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW();

CREATE INDEX IF NOT EXISTS ix_performance_archived_results_user_year
    ON performance_archived_results (user_id, period_year);
CREATE INDEX IF NOT EXISTS ix_performance_archived_results_personnel_year
    ON performance_archived_results (personnel_id, period_year);
CREATE INDEX IF NOT EXISTS ix_performance_archived_results_score
    ON performance_archived_results (score_value);

CREATE TABLE IF NOT EXISTS ai_decision_historical_archive_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    period_year INTEGER,
    record_count INTEGER DEFAULT 0,
    average_score NUMERIC(10,2),
    low_score_count INTEGER DEFAULT 0,
    high_score_count INTEGER DEFAULT 0,
    trend_label VARCHAR(180),
    risk_note VARCHAR(220),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ai_decision_historical_archive_snapshots_user_year
    ON ai_decision_historical_archive_snapshots (user_id, period_year);

DO $$
BEGIN
    IF to_regclass('public.module_settings') IS NOT NULL THEN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
             WHERE table_name='module_settings' AND column_name='label'
        ) THEN
            INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
            SELECT 'ai_decision', 'faz7_low_score_limit', 'Faz 7 düşük performans sınırı', '70', 'string', 'Geçmiş karne arşivi düşük performans alt sınırı.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz7_low_score_limit');

            INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
            SELECT 'ai_decision', 'faz7_high_score_limit', 'Faz 7 yüksek başarı sınırı', '90', 'string', 'Geçmiş karne arşivi yüksek başarı sınırı.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz7_high_score_limit');

            INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
            SELECT 'ai_decision', 'faz7_detail_for_personnel_only', 'Geçmiş karne detay koruması', 'true', 'boolean', 'Personel geçmiş karne detayının yetki kapsamında gösterilmesi.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz7_detail_for_personnel_only');

            INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
            SELECT 'ai_decision', 'faz7_manager_summary_only', 'Yönetici arşiv özeti', 'true', 'boolean', 'Yönetici arşiv ekranlarında kişi detayı yerine özet gösterimi.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz7_manager_summary_only');
        ELSE
            INSERT INTO module_settings (module_key, setting_key, value_text, description, is_active)
            SELECT 'ai_decision', 'faz7_low_score_limit', '70', 'Geçmiş karne arşivi düşük performans alt sınırı.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz7_low_score_limit');

            INSERT INTO module_settings (module_key, setting_key, value_text, description, is_active)
            SELECT 'ai_decision', 'faz7_high_score_limit', '90', 'Geçmiş karne arşivi yüksek başarı sınırı.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz7_high_score_limit');

            INSERT INTO module_settings (module_key, setting_key, value_text, description, is_active)
            SELECT 'ai_decision', 'faz7_detail_for_personnel_only', 'true', 'Personel geçmiş karne detayının yetki kapsamında gösterilmesi.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz7_detail_for_personnel_only');

            INSERT INTO module_settings (module_key, setting_key, value_text, description, is_active)
            SELECT 'ai_decision', 'faz7_manager_summary_only', 'true', 'Yönetici arşiv ekranlarında kişi detayı yerine özet gösterimi.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz7_manager_summary_only');
        END IF;
    END IF;
END $$;
