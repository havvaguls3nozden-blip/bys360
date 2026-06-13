-- İletişim ve Anket Rol Matrisi Onarımı
-- Amaç: Mesajlar/Bildirimler/Anketler herkese açık; Anket Yönetimi ve Sonuçları yönetici rollerinde açık.

BEGIN;

DELETE FROM user_menu_permissions
WHERE menu_key IN ('messages', 'notifications', 'surveys', 'survey_manage', 'survey_results');

DELETE FROM unit_menu_profiles
WHERE menu_key IN ('messages', 'notifications', 'surveys', 'survey_manage', 'survey_results');

WITH desired(role_name, menu_key, is_visible) AS (
    VALUES
        ('admin', 'messages', TRUE),
        ('admin', 'notifications', TRUE),
        ('admin', 'surveys', TRUE),
        ('admin', 'survey_manage', TRUE),
        ('admin', 'survey_results', TRUE),

        ('baskan', 'messages', TRUE),
        ('baskan', 'notifications', TRUE),
        ('baskan', 'surveys', TRUE),
        ('baskan', 'survey_manage', TRUE),
        ('baskan', 'survey_results', TRUE),

        ('baskan_yardimcisi', 'messages', TRUE),
        ('baskan_yardimcisi', 'notifications', TRUE),
        ('baskan_yardimcisi', 'surveys', TRUE),
        ('baskan_yardimcisi', 'survey_manage', TRUE),
        ('baskan_yardimcisi', 'survey_results', TRUE),

        ('grup_baskani', 'messages', TRUE),
        ('grup_baskani', 'notifications', TRUE),
        ('grup_baskani', 'surveys', TRUE),
        ('grup_baskani', 'survey_manage', TRUE),
        ('grup_baskani', 'survey_results', TRUE),

        ('mali_musavir', 'messages', TRUE),
        ('mali_musavir', 'notifications', TRUE),
        ('mali_musavir', 'surveys', TRUE),
        ('mali_musavir', 'survey_manage', TRUE),
        ('mali_musavir', 'survey_results', TRUE),

        ('koordinator', 'messages', TRUE),
        ('koordinator', 'notifications', TRUE),
        ('koordinator', 'surveys', TRUE),
        ('koordinator', 'survey_manage', TRUE),
        ('koordinator', 'survey_results', TRUE),

        ('birim_sorumlusu', 'messages', TRUE),
        ('birim_sorumlusu', 'notifications', TRUE),
        ('birim_sorumlusu', 'surveys', TRUE),
        ('birim_sorumlusu', 'survey_manage', TRUE),
        ('birim_sorumlusu', 'survey_results', TRUE),

        ('personel', 'messages', TRUE),
        ('personel', 'notifications', TRUE),
        ('personel', 'surveys', TRUE),
        ('personel', 'survey_manage', FALSE),
        ('personel', 'survey_results', FALSE)
)
INSERT INTO role_menu_defaults (role_name, menu_key, is_visible, source_type, updated_by_user_id, note, created_at, updated_at)
SELECT role_name, menu_key, is_visible, 'manual', NULL, 'communication-role-matrix-repair', NOW(), NOW()
FROM desired
ON CONFLICT (role_name, menu_key)
DO UPDATE SET
    is_visible = EXCLUDED.is_visible,
    source_type = EXCLUDED.source_type,
    updated_by_user_id = EXCLUDED.updated_by_user_id,
    note = EXCLUDED.note,
    updated_at = NOW();

COMMIT;
