-- BYS360_AI_DECISION_FAZ8_PERIOD_SCOPE_SQL_OK
-- Çoklu dönem, özel dönem ve kapsam karar destek ayarları.

ALTER TABLE performance_periods
    ADD COLUMN IF NOT EXISTS period_type VARCHAR(50) DEFAULT 'annual';

ALTER TABLE performance_periods
    ADD COLUMN IF NOT EXISTS scope_type VARCHAR(50) DEFAULT 'all';

ALTER TABLE performance_periods
    ADD COLUMN IF NOT EXISTS scope_reference VARCHAR(120);

ALTER TABLE performance_periods
    ADD COLUMN IF NOT EXISTS category_id INTEGER;

ALTER TABLE performance_periods
    ADD COLUMN IF NOT EXISTS unit_id INTEGER;

CREATE INDEX IF NOT EXISTS ix_performance_periods_period_type
    ON performance_periods (period_type);

CREATE INDEX IF NOT EXISTS ix_performance_periods_scope_type
    ON performance_periods (scope_type);

CREATE INDEX IF NOT EXISTS ix_performance_periods_dates
    ON performance_periods (start_date, end_date);

CREATE TABLE IF NOT EXISTS performance_period_scope_targets (
    id SERIAL PRIMARY KEY,
    period_id INTEGER NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id INTEGER,
    target_key VARCHAR(120),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_performance_period_scope_targets_period_id
    ON performance_period_scope_targets (period_id);

CREATE INDEX IF NOT EXISTS ix_performance_period_scope_targets_target
    ON performance_period_scope_targets (target_type, target_id);

CREATE TABLE IF NOT EXISTS ai_decision_period_scope_snapshots (
    id SERIAL PRIMARY KEY,
    period_id INTEGER,
    period_type VARCHAR(50),
    scope_type VARCHAR(50),
    assignment_count INTEGER DEFAULT 0,
    overlap_count INTEGER DEFAULT 0,
    attention_count INTEGER DEFAULT 0,
    risk_level VARCHAR(80),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ai_decision_period_scope_snapshots_period_id
    ON ai_decision_period_scope_snapshots (period_id);

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
SELECT 'ai_decision', 'faz8_allow_multiple_periods', 'Faz 8 Çoklu Dönem Aktif', 'true', 'boolean', 'Aynı yıl içinde birden fazla performans dönemi yönetimini destekler.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz8_allow_multiple_periods');

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
SELECT 'ai_decision', 'faz8_allow_special_periods', 'Faz 8 Özel Dönem Aktif', 'true', 'boolean', 'Kategori, birim veya seçili personel için özel dönem oluşturma karar destek ayarı.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz8_allow_special_periods');

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
SELECT 'ai_decision', 'faz8_require_scope_for_special_period', 'Faz 8 Özel Dönem Kapsam Zorunluluğu', 'true', 'boolean', 'Özel dönemlerde tüm kurum yerine dar kapsam seçimini önerir.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz8_require_scope_for_special_period');

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
SELECT 'ai_decision', 'faz8_overlap_warning_enabled', 'Faz 8 Tarih Çakışma Uyarısı', 'true', 'boolean', 'Aynı tarih aralığına yakın dönemlerde karar destek uyarısı üretir.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz8_overlap_warning_enabled');

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
SELECT 'ai_decision', 'faz8_selected_personnel_limit', 'Faz 8 Seçili Personel Üst Sınırı', '500', 'integer', 'Seçili personel kapsamı beklenenden genişse uyarı üretmek için kullanılır.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz8_selected_personnel_limit');

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
SELECT 'ai_decision', 'faz8_low_assignment_warning_limit', 'Faz 8 Görev Üretimi Alt Sınırı', '1', 'integer', 'Dönem için değerlendirme görevi yoksa karar destek uyarısı üretir.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz8_low_assignment_warning_limit');
