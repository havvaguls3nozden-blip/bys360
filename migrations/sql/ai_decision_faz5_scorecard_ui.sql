-- BYS360_AI_DECISION_FAZ5_SCORECARD_UI_SQL_OK
-- BYS360_AI_DECISION_FAZ5_MODULE_SETTINGS_LABEL_COMPAT_OK
-- Karne ve puanlama ekranları için karar destek ayarları.
-- module_settings.label NOT NULL şemalarıyla uyumludur.

CREATE TABLE IF NOT EXISTS ai_decision_scorecard_ui_snapshots (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER,
    period_id INTEGER,
    score_value NUMERIC(10,2),
    score_band VARCHAR(50),
    status_label VARCHAR(120),
    recommendation_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ai_decision_scorecard_ui_snapshots_evaluation_id
    ON ai_decision_scorecard_ui_snapshots (evaluation_id);

CREATE INDEX IF NOT EXISTS ix_ai_decision_scorecard_ui_snapshots_period_id
    ON ai_decision_scorecard_ui_snapshots (period_id);

INSERT INTO module_settings (module_key, setting_key, label, value_text, data_type, description, is_active)
SELECT 'ai_decision', 'faz5_low_score_limit', 'Düşük Performans Alt Sınırı', '70', 'string', 'Karne karar destek ekranı düşük performans alt sınırı.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz5_low_score_limit');

INSERT INTO module_settings (module_key, setting_key, label, value_text, data_type, description, is_active)
SELECT 'ai_decision', 'faz5_high_score_limit', 'Yüksek Başarı Sınırı', '90', 'string', 'Karne karar destek ekranı yüksek başarı sınırı.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz5_high_score_limit');

INSERT INTO module_settings (module_key, setting_key, label, value_text, data_type, description, is_active)
SELECT 'ai_decision', 'faz5_show_technical_terms', 'Teknik İfade Gösterimi', 'false', 'boolean', 'Karne ekranlarında teknik ifadeler gösterilmez.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz5_show_technical_terms');

INSERT INTO module_settings (module_key, setting_key, label, value_text, data_type, description, is_active)
SELECT 'ai_decision', 'faz5_require_low_score_explanation', 'Düşük Performans Açıklama Kontrolü', 'true', 'boolean', '70 altı sonuçlarda genel görüş kontrolü.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz5_require_low_score_explanation');

INSERT INTO module_settings (module_key, setting_key, label, value_text, data_type, description, is_active)
SELECT 'ai_decision', 'faz5_require_high_score_explanation', 'Yüksek Başarı Açıklama Kontrolü', 'true', 'boolean', '90 üstü sonuçlarda genel görüş kontrolü.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz5_require_high_score_explanation');
