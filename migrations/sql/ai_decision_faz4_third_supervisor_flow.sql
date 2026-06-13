-- BYS360 AI Karar Destek Faz 4 | 3. Amir Opsiyonelliği ve Akış Temizliği
-- Bu SQL mevcut kayıtları silmez; gerekli ayar ve denetim tablolarını güvenli şekilde ekler.

CREATE TABLE IF NOT EXISTS ai_decision_third_supervisor_flow_audit_logs (
    id SERIAL PRIMARY KEY,
    actor_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    evaluation_id INTEGER NULL,
    period_id INTEGER NULL,
    has_third_supervisor BOOLEAN NOT NULL DEFAULT FALSE,
    expected_action VARCHAR(40) NOT NULL DEFAULT 'none',
    status_label VARCHAR(160) NOT NULL DEFAULT 'Kontrol Edilmedi',
    warning_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ai_decision_third_supervisor_audit_eval ON ai_decision_third_supervisor_flow_audit_logs(evaluation_id);
CREATE INDEX IF NOT EXISTS ix_ai_decision_third_supervisor_audit_period ON ai_decision_third_supervisor_flow_audit_logs(period_id);
CREATE INDEX IF NOT EXISTS ix_ai_decision_third_supervisor_audit_actor ON ai_decision_third_supervisor_flow_audit_logs(actor_user_id);

INSERT INTO module_settings (module_key, setting_key, label, value_text, value_type, description, is_active, created_at, updated_at)
VALUES
('performance', 'third_supervisor_enabled', '3. Amir Kullanımı', 'true', 'bool', '3. amir yapısının sistemde kullanılabilmesini sağlar.', true, NOW(), NOW()),
('performance', 'third_supervisor_mode', '3. Amir Çalışma Şekli', 'comment', 'string', 'comment değerinde yalnızca görüş; score değerinde puan katkısı kullanılır.', true, NOW(), NOW()),
('performance', 'third_supervisor_show_column', '3. Amir Sütun Görünürlüğü', 'true', 'bool', '3. amir yalnızca gerekli kayıtlarda görünür.', true, NOW(), NOW()),
('performance', 'third_supervisor_weight_enabled', '3. Amir Puan Ağırlığı', 'false', 'bool', 'Yorum modunda kapalı, puan modunda açık kullanılmalıdır.', true, NOW(), NOW()),
('performance', 'default_first_supervisor_weight', '1. Amir Varsayılan Ağırlığı', '60', 'number', 'Standart iki amirli yapıda 1. amir ağırlığı.', true, NOW(), NOW()),
('performance', 'default_second_supervisor_weight', '2. Amir Varsayılan Ağırlığı', '40', 'number', 'Standart iki amirli yapıda 2. amir ağırlığı.', true, NOW(), NOW()),
('performance', 'default_third_supervisor_weight', '3. Amir Varsayılan Ağırlığı', '0', 'number', 'Yorum modunda 0 kalır; puan modunda kuruma göre ayarlanır.', true, NOW(), NOW()),
('ai_decision', 'faz4_third_supervisor_flow_enabled', '3. Amir Karar Destek Kontrolü', 'true', 'bool', 'Karar Destek Merkezi 3. amir akış sinyallerini üretir.', true, NOW(), NOW()),
('ai_decision', 'faz4_synthetic_task_guard_enabled', 'Gereksiz 3. Amir Bekleme Koruması', 'true', 'bool', '3. amir olmayan kayıt için bekleme izi oluşursa uyarı üretir.', true, NOW(), NOW()),
('ai_decision', 'faz4_empty_column_guard_enabled', 'Boş 3. Amir Sütun Koruması', 'true', 'bool', '3. amir olmayan listelerde boş sütun görünmesini engelleyen karar destek kuralını açar.', true, NOW(), NOW())
ON CONFLICT (module_key, setting_key) DO UPDATE SET
    label = EXCLUDED.label,
    value_type = EXCLUDED.value_type,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

INSERT INTO role_menu_defaults (role_name, menu_key, is_visible, source_type, note, created_at, updated_at)
VALUES
('admin', 'ai_decision.third_supervisor_flow', true, 'seed', 'Faz 4 3. amir akış karar destek görünürlüğü.', NOW(), NOW()),
('sistem_yoneticisi', 'ai_decision.third_supervisor_flow', true, 'seed', 'Faz 4 3. amir akış karar destek görünürlüğü.', NOW(), NOW()),
('baskan', 'ai_decision.third_supervisor_flow', true, 'seed', 'Faz 4 3. amir akış karar destek görünürlüğü.', NOW(), NOW()),
('personel_ve_destek_hizmetleri_grup_baskani', 'ai_decision.third_supervisor_flow', true, 'seed', 'Faz 4 3. amir akış karar destek görünürlüğü.', NOW(), NOW()),
('performans_yetkilisi', 'ai_decision.third_supervisor_flow', true, 'seed', 'Faz 4 3. amir akış karar destek görünürlüğü.', NOW(), NOW()),
('grup_baskani', 'ai_decision.third_supervisor_flow', true, 'seed', 'Faz 4 kendi kapsamı 3. amir akış görünürlüğü.', NOW(), NOW()),
('koordinator', 'ai_decision.third_supervisor_flow', true, 'seed', 'Faz 4 kendi kapsamı 3. amir akış görünürlüğü.', NOW(), NOW()),
('personel', 'ai_decision.third_supervisor_flow', false, 'seed', 'Standart personel 3. amir akış karar destek alanını görmez.', NOW(), NOW())
ON CONFLICT (role_name, menu_key) DO UPDATE SET
    is_visible = EXCLUDED.is_visible,
    source_type = EXCLUDED.source_type,
    note = EXCLUDED.note,
    updated_at = NOW();

-- BYS360_AI_DECISION_FAZ4_THIRD_SUPERVISOR_FLOW_SQL_OK
