-- BYS360_AI_DECISION_FAZ11_SQL_OK
-- Gelişim önerisi ve rehber alanı karar destek altyapısı.

CREATE TABLE IF NOT EXISTS ai_decision_development_guidance_snapshots (
    id SERIAL PRIMARY KEY,
    period_id INTEGER,
    personnel_id INTEGER,
    evaluation_id INTEGER,
    score_value NUMERIC(10,2),
    score_band VARCHAR(60),
    recommendation_count INTEGER DEFAULT 0,
    priority_label VARCHAR(60),
    safe_summary TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ai_decision_development_guidance_snapshots_period_id
    ON ai_decision_development_guidance_snapshots (period_id);

CREATE INDEX IF NOT EXISTS ix_ai_decision_development_guidance_snapshots_personnel_id
    ON ai_decision_development_guidance_snapshots (personnel_id);

CREATE INDEX IF NOT EXISTS ix_ai_decision_development_guidance_snapshots_evaluation_id
    ON ai_decision_development_guidance_snapshots (evaluation_id);

CREATE TABLE IF NOT EXISTS performance_development_recommendations (
    id SERIAL PRIMARY KEY,
    personnel_id INTEGER,
    period_id INTEGER,
    evaluation_id INTEGER,
    recommendation_text TEXT NOT NULL,
    followup_status VARCHAR(80) DEFAULT 'hazirlik',
    created_by INTEGER,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_performance_development_recommendations_personnel_id
    ON performance_development_recommendations (personnel_id);

CREATE INDEX IF NOT EXISTS ix_performance_development_recommendations_period_id
    ON performance_development_recommendations (period_id);

CREATE INDEX IF NOT EXISTS ix_performance_development_recommendations_evaluation_id
    ON performance_development_recommendations (evaluation_id);

DO $$
DECLARE
    has_module_settings BOOLEAN;
    has_label BOOLEAN;
    has_value_type BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = current_schema() AND table_name = 'module_settings'
    ) INTO has_module_settings;

    IF has_module_settings THEN
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = 'module_settings' AND column_name = 'label'
        ) INTO has_label;

        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = 'module_settings' AND column_name = 'value_type'
        ) INTO has_value_type;

        IF has_label AND has_value_type THEN
            INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
            SELECT 'ai_decision', 'faz11_development_guidance_enabled', 'Faz 11 Gelişim Önerisi', 'true', 'boolean', 'Gelişim önerisi ve rehber alanının karar destek merkezine bağlanması.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz11_development_guidance_enabled');

            INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
            SELECT 'ai_decision', 'faz11_no_administrative_decision', 'Faz 11 İdari Karar Üretmez', 'true', 'boolean', 'Gelişim önerileri idari karar yerine geçmez; insan denetimi esastır.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz11_no_administrative_decision');

            INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
            SELECT 'ai_decision', 'faz11_scorecard_panel_enabled', 'Faz 11 Karne Rehber Paneli', 'true', 'boolean', 'Karne ekranında gelişim önerisi rehber panelinin gösterilmesi.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz11_scorecard_panel_enabled');
        ELSIF has_label THEN
            INSERT INTO module_settings (module_key, setting_key, label, value_text, description, is_active)
            SELECT 'ai_decision', 'faz11_development_guidance_enabled', 'Faz 11 Gelişim Önerisi', 'true', 'Gelişim önerisi ve rehber alanının karar destek merkezine bağlanması.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz11_development_guidance_enabled');

            INSERT INTO module_settings (module_key, setting_key, label, value_text, description, is_active)
            SELECT 'ai_decision', 'faz11_no_administrative_decision', 'Faz 11 İdari Karar Üretmez', 'true', 'Gelişim önerileri idari karar yerine geçmez; insan denetimi esastır.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz11_no_administrative_decision');

            INSERT INTO module_settings (module_key, setting_key, label, value_text, description, is_active)
            SELECT 'ai_decision', 'faz11_scorecard_panel_enabled', 'Faz 11 Karne Rehber Paneli', 'true', 'Karne ekranında gelişim önerisi rehber panelinin gösterilmesi.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz11_scorecard_panel_enabled');
        ELSIF has_value_type THEN
            INSERT INTO module_settings (module_key, setting_key, value_text, value_type, description, is_active)
            SELECT 'ai_decision', 'faz11_development_guidance_enabled', 'true', 'boolean', 'Gelişim önerisi ve rehber alanının karar destek merkezine bağlanması.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz11_development_guidance_enabled');

            INSERT INTO module_settings (module_key, setting_key, value_text, value_type, description, is_active)
            SELECT 'ai_decision', 'faz11_no_administrative_decision', 'true', 'boolean', 'Gelişim önerileri idari karar yerine geçmez; insan denetimi esastır.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz11_no_administrative_decision');

            INSERT INTO module_settings (module_key, setting_key, value_text, value_type, description, is_active)
            SELECT 'ai_decision', 'faz11_scorecard_panel_enabled', 'true', 'boolean', 'Karne ekranında gelişim önerisi rehber panelinin gösterilmesi.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz11_scorecard_panel_enabled');
        ELSE
            INSERT INTO module_settings (module_key, setting_key, value_text, description, is_active)
            SELECT 'ai_decision', 'faz11_development_guidance_enabled', 'true', 'Gelişim önerisi ve rehber alanının karar destek merkezine bağlanması.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz11_development_guidance_enabled');

            INSERT INTO module_settings (module_key, setting_key, value_text, description, is_active)
            SELECT 'ai_decision', 'faz11_no_administrative_decision', 'true', 'Gelişim önerileri idari karar yerine geçmez; insan denetimi esastır.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz11_no_administrative_decision');

            INSERT INTO module_settings (module_key, setting_key, value_text, description, is_active)
            SELECT 'ai_decision', 'faz11_scorecard_panel_enabled', 'true', 'Karne ekranında gelişim önerisi rehber panelinin gösterilmesi.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz11_scorecard_panel_enabled');
        END IF;
    END IF;
END $$;
