-- BYS360_AI_DECISION_FAZ2_MIGRATION_SQL
-- Karar Destek Merkezi Faz 2: Personel kategori ve grup altyapısı.
-- PostgreSQL için idempotent SQL. SQLite/diğer ortamlar için apply script kullanılabilir.
-- setting key: ai_decision.category_group_enabled

CREATE TABLE IF NOT EXISTS personnel_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    code VARCHAR(80) NOT NULL UNIQUE,
    description VARCHAR(255),
    sort_order INTEGER NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS personnel_category VARCHAR(80) DEFAULT 'Diğer';
ALTER TABLE users ADD COLUMN IF NOT EXISTS performance_category_id INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_users_performance_category_id'
    ) THEN
        ALTER TABLE users
        ADD CONSTRAINT fk_users_performance_category_id
        FOREIGN KEY (performance_category_id) REFERENCES personnel_categories(id);
    END IF;
END $$;

INSERT INTO personnel_categories (code, name, description, sort_order, is_active)
VALUES
    ('guvenlik', 'Güvenlik', 'Güvenlik personel performans kategori grubu', 10, TRUE),
    ('temizlik', 'Temizlik', 'Temizlik personeli performans kategori grubu', 20, TRUE),
    ('idari_personel', 'İdari Personel', 'İdari personel performans kategori grubu', 30, TRUE),
    ('teknik_personel', 'Teknik Personel', 'Teknik personel performans kategori grubu', 40, TRUE),
    ('deneme_sureli_personel', 'Deneme Süreli Personel', 'Deneme süreli personel performans kategori grubu', 50, TRUE),
    ('diger', 'Diğer', 'Diğer personel performans kategori grubu', 60, TRUE)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    sort_order = EXCLUDED.sort_order,
    is_active = TRUE,
    updated_at = CURRENT_TIMESTAMP;

UPDATE users
   SET personnel_category = 'Diğer'
 WHERE personnel_category IS NULL OR TRIM(personnel_category) = '';

UPDATE users u
   SET performance_category_id = pc.id
  FROM personnel_categories pc
 WHERE u.performance_category_id IS NULL
   AND COALESCE(NULLIF(TRIM(u.personnel_category), ''), 'Diğer') = pc.name;

CREATE INDEX IF NOT EXISTS ix_users_personnel_category ON users(personnel_category);
CREATE INDEX IF NOT EXISTS ix_users_performance_category_id ON users(performance_category_id);
CREATE INDEX IF NOT EXISTS ix_personnel_categories_active_sort ON personnel_categories(is_active, sort_order);

CREATE TABLE IF NOT EXISTS ai_decision_category_group_snapshots (
    id SERIAL PRIMARY KEY,
    period_id INTEGER NULL,
    category_label VARCHAR(80) NOT NULL,
    employee_count INTEGER NOT NULL DEFAULT 0,
    evaluation_count INTEGER NOT NULL DEFAULT 0,
    published_count INTEGER NOT NULL DEFAULT 0,
    unpublished_count INTEGER NOT NULL DEFAULT 0,
    low_score_count INTEGER NOT NULL DEFAULT 0,
    high_score_count INTEGER NOT NULL DEFAULT 0,
    average_score NUMERIC(8,2) NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_ai_decision_category_group_snapshots_period ON ai_decision_category_group_snapshots(period_id);
CREATE INDEX IF NOT EXISTS ix_ai_decision_category_group_snapshots_category ON ai_decision_category_group_snapshots(category_label);

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
VALUES
    ('ai_decision', 'category_group_enabled', 'Kategori ve Grup Karar Desteği', 'true', 'boolean', 'Karar Destek Merkezi kategori/grup analiz motorunu açar veya kapatır.', TRUE),
    ('ai_decision', 'category_group_create_recommendations', 'Kategori Sinyali Öneri Kaydı', 'true', 'boolean', 'Kategori/grup risk sinyallerinden AI öneri kaydı oluşturur.', TRUE),
    ('performance', 'category_average_privacy_mode', 'Kategori Ortalama Gizliliği', 'aggregate_only', 'string', 'Kategori ortalaması kişi detayı göstermeden hesaplanır.', TRUE)
ON CONFLICT (module_key, setting_key) DO UPDATE SET
    label = EXCLUDED.label,
    value_type = EXCLUDED.value_type,
    description = EXCLUDED.description,
    is_active = TRUE;
