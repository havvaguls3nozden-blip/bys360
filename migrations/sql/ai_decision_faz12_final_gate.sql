-- BYS360_AI_DECISION_FAZ12_SQL_OK
-- Final Gate ve Canlı Hazırlık kayıtları.

CREATE TABLE IF NOT EXISTS ai_decision_final_gate_runs (
    id SERIAL PRIMARY KEY,
    gate_name VARCHAR(120) NOT NULL DEFAULT 'ai_decision_faz12_final_gate',
    ok BOOLEAN NOT NULL DEFAULT FALSE,
    error_count INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0,
    report_json TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ai_decision_final_gate_runs_created_at
    ON ai_decision_final_gate_runs (created_at);

CREATE TABLE IF NOT EXISTS ai_decision_release_check_items (
    id SERIAL PRIMARY KEY,
    check_key VARCHAR(160) NOT NULL UNIQUE,
    check_label VARCHAR(240) NOT NULL,
    check_group VARCHAR(80) NOT NULL DEFAULT 'final_gate',
    is_required BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

INSERT INTO ai_decision_release_check_items (check_key, check_label, check_group, is_required)
VALUES
('faz_1_11_gate_reports', 'Faz 1-11 gate raporları kontrol edildi', 'final_gate', TRUE),
('route_registration_integrity', 'Karar Destek route kayıtları açılış güvenliğiyle kontrol edildi', 'final_gate', TRUE),
('technical_language_cleanup', 'Kullanıcı ekranlarında teknik ifade temizliği kontrol edildi', 'final_gate', TRUE),
('module_settings_label_compat', 'module_settings label uyumu korundu', 'final_gate', TRUE),
('release_hygiene', 'Canlı paket hijyeni kontrol edildi', 'final_gate', TRUE)
ON CONFLICT (check_key) DO UPDATE SET
    check_label = EXCLUDED.check_label,
    check_group = EXCLUDED.check_group,
    is_required = EXCLUDED.is_required;
