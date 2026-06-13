-- BYS360_AI_DECISION_FAZ10_SQL_OK
-- Performans içi ara not / geri bildirim karar destek altyapısı.

CREATE TABLE IF NOT EXISTS ai_decision_interim_feedback_snapshots (
    id SERIAL PRIMARY KEY,
    period_id INTEGER,
    personnel_id INTEGER,
    evaluation_id INTEGER,
    total_notes INTEGER DEFAULT 0,
    positive_total INTEGER DEFAULT 0,
    negative_total INTEGER DEFAULT 0,
    development_need_total INTEGER DEFAULT 0,
    balance_label VARCHAR(220),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ai_decision_interim_feedback_snapshots_period_id
    ON ai_decision_interim_feedback_snapshots (period_id);

CREATE INDEX IF NOT EXISTS ix_ai_decision_interim_feedback_snapshots_personnel_id
    ON ai_decision_interim_feedback_snapshots (personnel_id);

CREATE INDEX IF NOT EXISTS ix_ai_decision_interim_feedback_snapshots_evaluation_id
    ON ai_decision_interim_feedback_snapshots (evaluation_id);

CREATE TABLE IF NOT EXISTS performance_interim_note_decision_snapshots (
    id SERIAL PRIMARY KEY,
    interim_note_id INTEGER,
    period_id INTEGER,
    personnel_id INTEGER,
    note_type VARCHAR(80),
    safe_label VARCHAR(160),
    decision_signal VARCHAR(120),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

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
            SELECT 'ai_decision', 'faz10_interim_feedback_enabled', 'Faz 10 Ara Not Karar Destek', 'true', 'boolean', 'Dönem içi notların karar destek özetine bağlanması.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz10_interim_feedback_enabled');

            INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
            SELECT 'ai_decision', 'faz10_auto_score_disabled', 'Faz 10 Otomatik Puan Kapalı', 'true', 'boolean', 'Ara notlar otomatik puan üretmez; yalnızca hatırlatma ve özet sağlar.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz10_auto_score_disabled');

            INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
            SELECT 'ai_decision', 'faz10_sensitive_text_guard', 'Faz 10 Hassas Metin Koruması', 'true', 'boolean', 'Ara not karar destek özetlerinde hassas içerik sınırlandırılır.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz10_sensitive_text_guard');
        ELSIF has_label THEN
            INSERT INTO module_settings (module_key, setting_key, label, value_text, description, is_active)
            SELECT 'ai_decision', 'faz10_interim_feedback_enabled', 'Faz 10 Ara Not Karar Destek', 'true', 'Dönem içi notların karar destek özetine bağlanması.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz10_interim_feedback_enabled');

            INSERT INTO module_settings (module_key, setting_key, label, value_text, description, is_active)
            SELECT 'ai_decision', 'faz10_auto_score_disabled', 'Faz 10 Otomatik Puan Kapalı', 'true', 'Ara notlar otomatik puan üretmez; yalnızca hatırlatma ve özet sağlar.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz10_auto_score_disabled');

            INSERT INTO module_settings (module_key, setting_key, label, value_text, description, is_active)
            SELECT 'ai_decision', 'faz10_sensitive_text_guard', 'Faz 10 Hassas Metin Koruması', 'true', 'Ara not karar destek özetlerinde hassas içerik sınırlandırılır.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz10_sensitive_text_guard');
        ELSIF has_value_type THEN
            INSERT INTO module_settings (module_key, setting_key, value_text, value_type, description, is_active)
            SELECT 'ai_decision', 'faz10_interim_feedback_enabled', 'true', 'boolean', 'Dönem içi notların karar destek özetine bağlanması.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz10_interim_feedback_enabled');

            INSERT INTO module_settings (module_key, setting_key, value_text, value_type, description, is_active)
            SELECT 'ai_decision', 'faz10_auto_score_disabled', 'true', 'boolean', 'Ara notlar otomatik puan üretmez; yalnızca hatırlatma ve özet sağlar.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz10_auto_score_disabled');

            INSERT INTO module_settings (module_key, setting_key, value_text, value_type, description, is_active)
            SELECT 'ai_decision', 'faz10_sensitive_text_guard', 'true', 'boolean', 'Ara not karar destek özetlerinde hassas içerik sınırlandırılır.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz10_sensitive_text_guard');
        ELSE
            INSERT INTO module_settings (module_key, setting_key, value_text, description, is_active)
            SELECT 'ai_decision', 'faz10_interim_feedback_enabled', 'true', 'Dönem içi notların karar destek özetine bağlanması.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz10_interim_feedback_enabled');

            INSERT INTO module_settings (module_key, setting_key, value_text, description, is_active)
            SELECT 'ai_decision', 'faz10_auto_score_disabled', 'true', 'Ara notlar otomatik puan üretmez; yalnızca hatırlatma ve özet sağlar.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz10_auto_score_disabled');

            INSERT INTO module_settings (module_key, setting_key, value_text, description, is_active)
            SELECT 'ai_decision', 'faz10_sensitive_text_guard', 'true', 'Ara not karar destek özetlerinde hassas içerik sınırlandırılır.', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz10_sensitive_text_guard');
        END IF;
    END IF;
END $$;
