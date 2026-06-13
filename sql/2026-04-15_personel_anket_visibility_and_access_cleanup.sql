-- BYS360 personel anket görünürlük ve erişim temizliği
BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'user_menu_permissions'
    ) THEN
        DELETE FROM user_menu_permissions
        WHERE menu_key IN ('survey_manage', 'survey_results')
          AND user_id IN (
              SELECT id FROM users WHERE lower(coalesce(role, '')) = 'personel'
          );

        DELETE FROM user_menu_permissions
        WHERE menu_key = 'surveys'
          AND coalesce(is_visible, false) = false
          AND user_id IN (
              SELECT id FROM users WHERE lower(coalesce(role, '')) = 'personel'
          );
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'role_menu_defaults'
    ) THEN
        DELETE FROM role_menu_defaults
        WHERE lower(coalesce(role_name, '')) = 'personel'
          AND menu_key IN ('survey_manage', 'survey_results');

        INSERT INTO role_menu_defaults (role_name, menu_key, is_visible, source_type)
        VALUES ('personel', 'surveys', true, 'overlay_fix')
        ON CONFLICT (role_name, menu_key)
        DO UPDATE SET is_visible = EXCLUDED.is_visible, source_type = EXCLUDED.source_type;
    END IF;
END $$;

COMMIT;
