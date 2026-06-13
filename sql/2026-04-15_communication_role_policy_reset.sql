-- İletişim ve anket ailesi için rol bazlı varsayılanları tekrar devreye alır.
-- Kullanıcı bazlı eski override kayıtlarını siler; böylece yeni rol politikası görünür hale gelir.

DELETE FROM user_menu_permissions
WHERE menu_key IN (
    'messages',
    'notifications',
    'surveys',
    'survey_manage',
    'survey_results'
);

DELETE FROM role_menu_defaults
WHERE menu_key IN (
    'messages',
    'notifications',
    'surveys',
    'survey_manage',
    'survey_results'
);

INSERT INTO role_menu_defaults (role_name, menu_key, is_visible, source_type, note, created_at, updated_at) VALUES
('admin', 'messages', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('admin', 'notifications', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('admin', 'surveys', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('admin', 'survey_manage', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('admin', 'survey_results', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),

('baskan', 'messages', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('baskan', 'notifications', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('baskan', 'surveys', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('baskan', 'survey_manage', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('baskan', 'survey_results', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),

('baskan_yardimcisi', 'messages', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('baskan_yardimcisi', 'notifications', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('baskan_yardimcisi', 'surveys', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('baskan_yardimcisi', 'survey_manage', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('baskan_yardimcisi', 'survey_results', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),

('grup_baskani', 'messages', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('grup_baskani', 'notifications', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('grup_baskani', 'surveys', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('grup_baskani', 'survey_manage', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('grup_baskani', 'survey_results', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),

('mali_musavir', 'messages', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('mali_musavir', 'notifications', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('mali_musavir', 'surveys', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('mali_musavir', 'survey_manage', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('mali_musavir', 'survey_results', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),

('koordinator', 'messages', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('koordinator', 'notifications', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('koordinator', 'surveys', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('koordinator', 'survey_manage', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('koordinator', 'survey_results', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),

('birim_sorumlusu', 'messages', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('birim_sorumlusu', 'notifications', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('birim_sorumlusu', 'surveys', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('birim_sorumlusu', 'survey_manage', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('birim_sorumlusu', 'survey_results', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),

('personel', 'messages', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('personel', 'notifications', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('personel', 'surveys', true, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('personel', 'survey_manage', false, 'manual', 'communication-role-policy-reset', NOW(), NOW()),
('personel', 'survey_results', false, 'manual', 'communication-role-policy-reset', NOW(), NOW())
ON CONFLICT (role_name, menu_key) DO UPDATE
SET is_visible = EXCLUDED.is_visible,
    source_type = EXCLUDED.source_type,
    note = EXCLUDED.note,
    updated_at = NOW();
