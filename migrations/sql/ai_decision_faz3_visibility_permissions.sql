-- BYS360 AI Karar Destek Faz 3 | Görünürlük ve Yetki Sınırları
-- Bu SQL güvenli seed mantığıyla çalışır; mevcut kayıtları ezmez.

CREATE TABLE IF NOT EXISTS ai_decision_visibility_audit_logs (
    id SERIAL PRIMARY KEY,
    actor_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    target_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    target_table VARCHAR(120) NULL,
    target_id INTEGER NULL,
    access_scope VARCHAR(80) NOT NULL DEFAULT 'unknown',
    access_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    access_reason TEXT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ai_decision_visibility_audit_actor ON ai_decision_visibility_audit_logs(actor_user_id);
CREATE INDEX IF NOT EXISTS ix_ai_decision_visibility_audit_target ON ai_decision_visibility_audit_logs(target_table, target_id);
CREATE INDEX IF NOT EXISTS ix_ai_decision_visibility_audit_scope ON ai_decision_visibility_audit_logs(access_scope);

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active, created_at, updated_at)
VALUES
('ai_decision', 'faz3_visibility_guard_enabled', 'Karar Destek Görünürlük Koruması', 'true', 'bool', 'Karar Destek Merkezi route ve veri kapsamı kontrolünü etkinleştirir.', true, NOW(), NOW()),
('ai_decision', 'faz3_personnel_detail_for_personnel', 'Personel İçin Kişi Detayı', 'false', 'bool', 'Standart personel rolünde karar destek kişi detayı açılmasını engeller.', true, NOW(), NOW()),
('ai_decision', 'faz3_scope_mode', 'Karar Destek Kapsam Modu', 'role_unit_category', 'string', 'Rol, birim, üst birim ve kategoriye göre karar destek görünürlüğü uygular.', true, NOW(), NOW())
ON CONFLICT (module_key, setting_key) DO UPDATE SET
    label = EXCLUDED.label,
    value_type = EXCLUDED.value_type,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

INSERT INTO role_menu_defaults (role_name, menu_key, is_visible, source_type, note, created_at, updated_at)
VALUES
('admin', 'ai_decision_center', true, 'seed', 'Faz 3 karar destek merkezi genel görünürlük.', NOW(), NOW()),
('sistem_yoneticisi', 'ai_decision_center', true, 'seed', 'Faz 3 karar destek merkezi genel görünürlük.', NOW(), NOW()),
('baskan', 'ai_decision_center', true, 'seed', 'Faz 3 karar destek merkezi üst yönetim görünürlüğü.', NOW(), NOW()),
('personel_ve_destek_hizmetleri_grup_baskani', 'ai_decision_center', true, 'seed', 'Faz 3 yayın ön kontrol ve karar destek görünürlüğü.', NOW(), NOW()),
('performans_yetkilisi', 'ai_decision_center', true, 'seed', 'Faz 3 performans karar destek görünürlüğü.', NOW(), NOW()),
('grup_baskani', 'ai_decision_center', true, 'seed', 'Faz 3 kendi kapsamı karar destek görünürlüğü.', NOW(), NOW()),
('koordinator', 'ai_decision_center', true, 'seed', 'Faz 3 kendi kapsamı karar destek görünürlüğü.', NOW(), NOW()),
('personel', 'ai_decision_center', false, 'seed', 'Standart personel karar destek kişi detayını görmez.', NOW(), NOW())
ON CONFLICT (role_name, menu_key) DO UPDATE SET
    is_visible = EXCLUDED.is_visible,
    source_type = EXCLUDED.source_type,
    note = EXCLUDED.note,
    updated_at = NOW();

-- BYS360_AI_DECISION_FAZ3_VISIBILITY_PERMISSIONS_SQL_OK
