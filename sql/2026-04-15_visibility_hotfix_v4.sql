-- 2026-04-15_visibility_hotfix_v4.sql

INSERT INTO role_menu_defaults (role_name, menu_key, is_visible)
VALUES
    ('admin', 'messages', TRUE),
    ('admin', 'surveys', TRUE),
    ('admin', 'survey_manage', TRUE),
    ('admin', 'survey_results', TRUE),

    ('baskan', 'messages', TRUE),
    ('baskan', 'surveys', TRUE),
    ('baskan', 'survey_manage', TRUE),
    ('baskan', 'survey_results', TRUE),

    ('baskan_yardimcisi', 'messages', TRUE),
    ('baskan_yardimcisi', 'surveys', TRUE),
    ('baskan_yardimcisi', 'survey_manage', TRUE),
    ('baskan_yardimcisi', 'survey_results', TRUE),

    ('grup_baskani', 'messages', TRUE),
    ('grup_baskani', 'surveys', TRUE),
    ('grup_baskani', 'survey_manage', TRUE),
    ('grup_baskani', 'survey_results', TRUE),

    ('mali_musavir', 'messages', TRUE),
    ('mali_musavir', 'surveys', TRUE),
    ('mali_musavir', 'survey_manage', TRUE),
    ('mali_musavir', 'survey_results', TRUE),

    ('koordinator', 'messages', TRUE),
    ('koordinator', 'surveys', TRUE),
    ('koordinator', 'survey_manage', TRUE),
    ('koordinator', 'survey_results', TRUE),

    ('birim_sorumlusu', 'messages', TRUE),
    ('birim_sorumlusu', 'surveys', TRUE),
    ('birim_sorumlusu', 'survey_manage', TRUE),
    ('birim_sorumlusu', 'survey_results', TRUE),

    ('personel', 'messages', TRUE),
    ('personel', 'surveys', TRUE),
    ('personel', 'survey_manage', FALSE),
    ('personel', 'survey_results', FALSE)
ON CONFLICT (role_name, menu_key)
DO UPDATE SET is_visible = EXCLUDED.is_visible;

UPDATE user_menu_permissions ump
SET is_visible = FALSE
FROM users u
WHERE u.id = ump.user_id
  AND lower(coalesce(u.role, '')) = 'personel'
  AND ump.menu_key IN ('survey_manage', 'survey_results');

UPDATE user_menu_permissions ump
SET is_visible = TRUE
FROM users u
WHERE u.id = ump.user_id
  AND lower(coalesce(u.role, '')) = 'personel'
  AND ump.menu_key IN ('messages', 'surveys');

UPDATE user_menu_permissions ump
SET is_visible = TRUE
FROM users u
WHERE u.id = ump.user_id
  AND lower(coalesce(u.role, '')) = 'admin'
  AND ump.menu_key IN ('messages', 'surveys', 'survey_manage', 'survey_results');

UPDATE user_menu_permissions ump
SET is_visible = TRUE
FROM users u
WHERE u.id = ump.user_id
  AND lower(coalesce(u.role, '')) IN (
      'baskan',
      'baskan_yardimcisi',
      'grup_baskani',
      'mali_musavir',
      'koordinator',
      'birim_sorumlusu'
  )
  AND ump.menu_key IN ('messages', 'surveys', 'survey_manage', 'survey_results');
