-- BYS360 cekirdek menu onarimi
-- Mesajlar ve anketler kaybolmasin; yonetim ve rapor menuleri rol bazli geri acilsin.

BEGIN;

-- 1) Rol varsayilanlarini cekirdek kurala gore duzelt
WITH role_key_matrix(role_name, menu_key, is_visible) AS (
    VALUES
        ('admin', 'messages', TRUE),
        ('baskan', 'messages', TRUE),
        ('baskan_yardimcisi', 'messages', TRUE),
        ('grup_baskani', 'messages', TRUE),
        ('mali_musavir', 'messages', TRUE),
        ('koordinator', 'messages', TRUE),
        ('birim_sorumlusu', 'messages', TRUE),
        ('personel', 'messages', TRUE),

        ('admin', 'notifications', TRUE),
        ('baskan', 'notifications', TRUE),
        ('baskan_yardimcisi', 'notifications', TRUE),
        ('grup_baskani', 'notifications', TRUE),
        ('mali_musavir', 'notifications', TRUE),
        ('koordinator', 'notifications', TRUE),
        ('birim_sorumlusu', 'notifications', TRUE),
        ('personel', 'notifications', TRUE),

        ('admin', 'surveys', TRUE),
        ('baskan', 'surveys', TRUE),
        ('baskan_yardimcisi', 'surveys', TRUE),
        ('grup_baskani', 'surveys', TRUE),
        ('mali_musavir', 'surveys', TRUE),
        ('koordinator', 'surveys', TRUE),
        ('birim_sorumlusu', 'surveys', TRUE),
        ('personel', 'surveys', TRUE),

        ('admin', 'survey_manage', TRUE),
        ('baskan', 'survey_manage', TRUE),
        ('baskan_yardimcisi', 'survey_manage', TRUE),
        ('grup_baskani', 'survey_manage', TRUE),
        ('mali_musavir', 'survey_manage', TRUE),
        ('koordinator', 'survey_manage', TRUE),
        ('birim_sorumlusu', 'survey_manage', TRUE),
        ('personel', 'survey_manage', FALSE),

        ('admin', 'survey_results', TRUE),
        ('baskan', 'survey_results', TRUE),
        ('baskan_yardimcisi', 'survey_results', TRUE),
        ('grup_baskani', 'survey_results', TRUE),
        ('mali_musavir', 'survey_results', TRUE),
        ('koordinator', 'survey_results', TRUE),
        ('birim_sorumlusu', 'survey_results', TRUE),
        ('personel', 'survey_results', FALSE),

        ('admin', 'performance_reports', TRUE),
        ('baskan', 'performance_reports', TRUE),
        ('baskan_yardimcisi', 'performance_reports', TRUE),
        ('grup_baskani', 'performance_reports', TRUE),
        ('mali_musavir', 'performance_reports', TRUE),
        ('koordinator', 'performance_reports', TRUE),
        ('birim_sorumlusu', 'performance_reports', TRUE),
        ('personel', 'performance_reports', FALSE)
)
INSERT INTO role_menu_defaults (role_name, menu_key, is_visible, source_type, updated_by_user_id, created_at, updated_at)
SELECT role_name, menu_key, is_visible, 'overlay_v8', NULL, NOW(), NOW()
FROM role_key_matrix
ON CONFLICT (role_name, menu_key)
DO UPDATE SET
    is_visible = EXCLUDED.is_visible,
    source_type = 'overlay_v8',
    updated_at = NOW();

-- 2) Bozuk kullanici override'larini cekirdek politika ile uyumlu hale getir
UPDATE user_menu_permissions ump
SET is_visible = TRUE, updated_at = NOW()
FROM users u
WHERE u.id = ump.user_id
  AND LOWER(COALESCE(u.role, '')) IN ('admin','baskan','baskan_yardimcisi','grup_baskani','mali_musavir','koordinator','birim_sorumlusu','personel')
  AND ump.menu_key IN ('messages','notifications','surveys')
  AND COALESCE(ump.is_visible, FALSE) = FALSE;

UPDATE user_menu_permissions ump
SET is_visible = TRUE, updated_at = NOW()
FROM users u
WHERE u.id = ump.user_id
  AND LOWER(COALESCE(u.role, '')) IN ('admin','baskan','baskan_yardimcisi','grup_baskani','mali_musavir','koordinator','birim_sorumlusu')
  AND ump.menu_key IN ('survey_manage','survey_results','performance_reports')
  AND COALESCE(ump.is_visible, FALSE) = FALSE;

UPDATE user_menu_permissions ump
SET is_visible = FALSE, updated_at = NOW()
FROM users u
WHERE u.id = ump.user_id
  AND LOWER(COALESCE(u.role, '')) = 'personel'
  AND ump.menu_key IN ('survey_manage','survey_results','performance_reports')
  AND COALESCE(ump.is_visible, TRUE) = TRUE;

COMMIT;
