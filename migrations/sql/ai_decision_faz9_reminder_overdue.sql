-- BYS360_AI_DECISION_FAZ9_REMINDER_SQL_OK
-- Otomatik hatırlatma, aksatan amir ve karar destek ayarları.

ALTER TABLE evaluation_assignments
    ADD COLUMN IF NOT EXISTS due_date DATE;

ALTER TABLE evaluation_assignments
    ADD COLUMN IF NOT EXISTS reminder_sent_at TIMESTAMP WITHOUT TIME ZONE;

ALTER TABLE evaluation_assignments
    ADD COLUMN IF NOT EXISTS reminder_count INTEGER DEFAULT 0;

ALTER TABLE evaluation_assignments
    ADD COLUMN IF NOT EXISTS overdue_flag BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS ix_evaluation_assignments_due_date
    ON evaluation_assignments (due_date);

CREATE INDEX IF NOT EXISTS ix_evaluation_assignments_overdue_flag
    ON evaluation_assignments (overdue_flag);

CREATE TABLE IF NOT EXISTS ai_decision_reminder_snapshots (
    id SERIAL PRIMARY KEY,
    period_id INTEGER,
    evaluator_id INTEGER,
    assignment_count INTEGER DEFAULT 0,
    pending_count INTEGER DEFAULT 0,
    due_soon_count INTEGER DEFAULT 0,
    overdue_count INTEGER DEFAULT 0,
    critical_overdue_count INTEGER DEFAULT 0,
    missing_due_date_count INTEGER DEFAULT 0,
    risk_level VARCHAR(80),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ai_decision_reminder_snapshots_period_id
    ON ai_decision_reminder_snapshots (period_id);

CREATE INDEX IF NOT EXISTS ix_ai_decision_reminder_snapshots_evaluator_id
    ON ai_decision_reminder_snapshots (evaluator_id);

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
SELECT 'ai_decision', 'faz9_reminders_enabled', 'Faz 9 Hatırlatma Takibi Aktif', 'true', 'boolean', 'Değerlendirme görevlerinde son tarih ve gecikme karar destek özetlerini etkinleştirir.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz9_reminders_enabled');

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
SELECT 'ai_decision', 'faz9_reminder_before_days', 'Faz 9 Hatırlatma Gün Eşiği', '3', 'integer', 'Son tarihe kaç gün kala hatırlatma önerisi üretileceğini belirler.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz9_reminder_before_days');

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
SELECT 'ai_decision', 'faz9_overdue_after_days', 'Faz 9 Gecikme Başlangıç Eşiği', '1', 'integer', 'Son tarih geçtikten kaç gün sonra görev gecikmiş kabul edilir.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz9_overdue_after_days');

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
SELECT 'ai_decision', 'faz9_critical_overdue_days', 'Faz 9 Kritik Gecikme Eşiği', '7', 'integer', 'Gecikmiş değerlendirmelerin kritik takip seviyesine alınacağı gün eşiği.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz9_critical_overdue_days');

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
SELECT 'ai_decision', 'faz9_max_detail_rows', 'Faz 9 Özet Satır Sınırı', '250', 'integer', 'Aksatan amir yoğunluğu özetinde gösterilecek en yüksek satır sayısı.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz9_max_detail_rows');

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
SELECT 'ai_decision', 'faz9_send_email_if_enabled', 'Faz 9 E-posta Hatırlatma İzni', 'false', 'boolean', 'E-posta hatırlatma üretimi yetkili kullanıcı onayıyla açılabilir.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz9_send_email_if_enabled');

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active)
SELECT 'ai_decision', 'faz9_create_notification_if_enabled', 'Faz 9 Sistem İçi Bildirim İzni', 'true', 'boolean', 'Sistem içi hatırlatma bildirimleri için karar destek ayarı.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM module_settings WHERE module_key='ai_decision' AND setting_key='faz9_create_notification_if_enabled');
