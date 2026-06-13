-- BYS360 AI Karar Destek Faz 1 — Karar motoru ayar ve log hazırlığı
-- Güvenli/idempotent SQL. Mevcut AI tablolarını bozmaz.
-- BYS360_AI_DECISION_FAZ1_MIGRATION_SQL

CREATE TABLE IF NOT EXISTS ai_decision_engine_runs (
    id SERIAL PRIMARY KEY,
    module_type VARCHAR(50) NOT NULL DEFAULT 'performance',
    target_table VARCHAR(100) NOT NULL,
    target_id INTEGER NOT NULL,
    risk_score NUMERIC(6,2) NOT NULL DEFAULT 0,
    tone VARCHAR(30) NOT NULL DEFAULT 'info',
    summary_text TEXT,
    signal_count INTEGER NOT NULL DEFAULT 0,
    recommendation_count INTEGER NOT NULL DEFAULT 0,
    policy_json TEXT,
    created_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ai_decision_engine_runs_target
    ON ai_decision_engine_runs(module_type, target_table, target_id);
CREATE INDEX IF NOT EXISTS ix_ai_decision_engine_runs_created_at
    ON ai_decision_engine_runs(created_at);

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active, created_at, updated_at)
VALUES
('ai_decision', 'ai_decision.performance_engine_enabled', 'Performans karar motoru', 'true', 'boolean', 'Karar Destek Merkezi Faz 1 performans kural motorunu açar/kapatır.', true, NOW(), NOW()),
('ai_decision', 'ai_decision.manager_score_variance_threshold', 'Amir puan farkı eşiği', '3', 'number', 'Kriter bazında amirler arası dikkat sinyali için 1-5 ölçeğinde fark eşiği.', true, NOW(), NOW()),
('performance', 'performance_scoring.low_score_threshold', 'Düşük performans eşiği', '70', 'number', '70 altı sonuçlar Başkan/Üst Onay karar destek sinyali üretir.', true, NOW(), NOW()),
('performance', 'performance_scoring.high_score_threshold', 'Çok başarılı performans eşiği', '90', 'number', '90 üstü sonuçlarda ayrıntılı genel görüş kontrolü yapılır.', true, NOW(), NOW()),
('performance', 'performance_scoring.require_general_comment_below_70', '70 altı genel görüş zorunluluğu', 'true', 'boolean', '70 altı sonuçlarda ayrıntılı genel görüş kontrolünü açık tutar.', true, NOW(), NOW()),
('performance', 'performance_scoring.require_general_comment_above_90', '90 üstü genel görüş zorunluluğu', 'true', 'boolean', '90 üstü sonuçlarda ayrıntılı genel görüş kontrolünü açık tutar.', true, NOW(), NOW()),
('performance', 'performance_scoring.require_comment_for_score_1', '1 puan gerekçe zorunluluğu', 'true', 'boolean', '1 puan verildiğinde gerekçe kontrolünü açar/kapatır.', true, NOW(), NOW()),
('performance', 'performance_scoring.require_comment_for_score_5', '5 puan gerekçe zorunluluğu', 'true', 'boolean', '5 puan verildiğinde gerekçe kontrolünü açar/kapatır.', true, NOW(), NOW()),
('performance', 'performance_flow.low_score_requires_president_approval', '70 altı Başkan/Üst Onay', 'true', 'boolean', '70 altı sonuçlarda Başkan/Üst Onay karar destek sinyali üretir.', true, NOW(), NOW()),
('performance', 'performance_flow.low_score_publish_lock', '70 altı yayın kilidi', 'true', 'boolean', '70 altı kayıtların yayın görünürlüğünde onay kontrolünü vurgular.', true, NOW(), NOW())
ON CONFLICT (module_key, setting_key) DO UPDATE SET
    label = EXCLUDED.label,
    description = EXCLUDED.description,
    value_type = EXCLUDED.value_type,
    is_active = TRUE,
    updated_at = NOW();
