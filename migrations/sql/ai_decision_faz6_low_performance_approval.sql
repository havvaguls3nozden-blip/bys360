-- BYS360_AI_DECISION_FAZ6_LOW_PERFORMANCE_APPROVAL_SQL_OK
-- Başkan/Üst Onay ve düşük performans karar destek ayarları.

CREATE TABLE IF NOT EXISTS ai_decision_low_performance_process_snapshots (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER,
    user_id INTEGER,
    period_id INTEGER,
    final_score NUMERIC(10,2),
    requires_upper_approval BOOLEAN DEFAULT FALSE,
    upper_approval_completed BOOLEAN DEFAULT FALSE,
    publish_locked BOOLEAN DEFAULT FALSE,
    repeat_level VARCHAR(80),
    status_label VARCHAR(160),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ai_decision_low_perf_snapshots_evaluation_id
    ON ai_decision_low_performance_process_snapshots (evaluation_id);

CREATE INDEX IF NOT EXISTS ix_ai_decision_low_perf_snapshots_user_id
    ON ai_decision_low_performance_process_snapshots (user_id);

CREATE INDEX IF NOT EXISTS ix_ai_decision_low_perf_snapshots_period_id
    ON ai_decision_low_performance_process_snapshots (period_id);

DO $$
DECLARE
    has_label BOOLEAN;
    has_value_type BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'module_settings' AND column_name = 'label'
    ) INTO has_label;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'module_settings' AND column_name = 'value_type'
    ) INTO has_value_type;

    IF has_label AND has_value_type THEN
        INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
        SELECT 'ai_decision', seed.setting_key, seed.label, seed.value_text, 'string', seed.description, TRUE
          FROM (VALUES
            ('faz6_low_score_limit', 'Faz 6 düşük performans sınırı', '70', 'Düşük performans üst onay sınırı.'),
            ('faz6_high_score_limit', 'Faz 6 yüksek başarı sınırı', '90', 'Yüksek başarı karar destek sınırı.'),
            ('faz6_direct_upper_approval', 'Düşük performans doğrudan üst onay', 'true', '70 altı kayıtlar doğrudan Başkan/Üst Onay ekranına düşer.'),
            ('faz6_require_low_score_general_comment', '70 altı genel görüş zorunluluğu', 'true', '70 altı sonuçlarda ayrıntılı genel görüş aranır.'),
            ('faz6_publish_lock_until_upper_approval', 'Üst onay tamamlanmadan yayın kilidi', 'true', 'Onay tamamlanmadan personel görünürlüğü açılmaz.'),
            ('faz6_create_first_low_warning', 'İlk düşük performans uyarısı', 'true', 'Aynı yıl ilk 70 altı kayıtta uyarı süreci görünür olur.'),
            ('faz6_create_repeat_low_process', 'Tekrarlayan düşük performans süreci', 'true', 'Aynı yıl tekrar eden 70 altı kayıtta idari süreç sinyali oluşur.'),
            ('faz6_hr_admin_observer_mode', 'İK/Admin takip modu', 'true', 'İK/Admin ara onay kapısı olmadan takip ve yayın hazırlığı yapar.')
          ) AS seed(setting_key, label, value_text, description)
         WHERE NOT EXISTS (
            SELECT 1 FROM module_settings
             WHERE module_key = 'ai_decision' AND setting_key = seed.setting_key
         );
    ELSIF has_label THEN
        INSERT INTO module_settings (module_key, setting_key, label, value_text, description, is_active)
        SELECT 'ai_decision', seed.setting_key, seed.label, seed.value_text, seed.description, TRUE
          FROM (VALUES
            ('faz6_low_score_limit', 'Faz 6 düşük performans sınırı', '70', 'Düşük performans üst onay sınırı.'),
            ('faz6_direct_upper_approval', 'Düşük performans doğrudan üst onay', 'true', '70 altı kayıtlar doğrudan Başkan/Üst Onay ekranına düşer.'),
            ('faz6_publish_lock_until_upper_approval', 'Üst onay tamamlanmadan yayın kilidi', 'true', 'Onay tamamlanmadan personel görünürlüğü açılmaz.')
          ) AS seed(setting_key, label, value_text, description)
         WHERE NOT EXISTS (
            SELECT 1 FROM module_settings
             WHERE module_key = 'ai_decision' AND setting_key = seed.setting_key
         );
    ELSE
        INSERT INTO module_settings (module_key, setting_key, value_text, description, is_active)
        SELECT 'ai_decision', seed.setting_key, seed.value_text, seed.description, TRUE
          FROM (VALUES
            ('faz6_low_score_limit', '70', 'Düşük performans üst onay sınırı.'),
            ('faz6_direct_upper_approval', 'true', '70 altı kayıtlar doğrudan Başkan/Üst Onay ekranına düşer.'),
            ('faz6_publish_lock_until_upper_approval', 'true', 'Onay tamamlanmadan personel görünürlüğü açılmaz.')
          ) AS seed(setting_key, value_text, description)
         WHERE NOT EXISTS (
            SELECT 1 FROM module_settings
             WHERE module_key = 'ai_decision' AND setting_key = seed.setting_key
         );
    END IF;
END $$;
