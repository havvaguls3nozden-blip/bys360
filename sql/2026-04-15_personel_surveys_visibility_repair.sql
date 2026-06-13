-- BYS360 | Personel anket görünürlüğü ve erişim onarımı
-- Amaç:
-- 1) personelde "surveys" açık olsun
-- 2) personelde survey_manage / survey_results kapalı kalsın
-- 3) eski kullanıcı override kayıtları temizlensin
-- 4) yanlış kapatılmış birim profilleri surveys için tekrar açılsın

BEGIN;

INSERT INTO role_menu_defaults (role_name, menu_key, is_visible, source_type, note)
VALUES ('personel', 'surveys', TRUE, 'overlay_fix', 'Atanmış anket erişimi için görünür bırakıldı')
ON CONFLICT (role_name, menu_key)
DO UPDATE SET
    is_visible = EXCLUDED.is_visible,
    source_type = EXCLUDED.source_type,
    note = EXCLUDED.note;

INSERT INTO role_menu_defaults (role_name, menu_key, is_visible, source_type, note)
VALUES ('personel', 'survey_manage', FALSE, 'overlay_fix', 'Personelde anket yönetimi kapalı')
ON CONFLICT (role_name, menu_key)
DO UPDATE SET
    is_visible = EXCLUDED.is_visible,
    source_type = EXCLUDED.source_type,
    note = EXCLUDED.note;

INSERT INTO role_menu_defaults (role_name, menu_key, is_visible, source_type, note)
VALUES ('personel', 'survey_results', FALSE, 'overlay_fix', 'Personelde anket sonuçları kapalı')
ON CONFLICT (role_name, menu_key)
DO UPDATE SET
    is_visible = EXCLUDED.is_visible,
    source_type = EXCLUDED.source_type,
    note = EXCLUDED.note;

DELETE FROM user_menu_permissions ump
USING users u
WHERE u.id = ump.user_id
  AND lower(coalesce(u.role, '')) = 'personel'
  AND ump.menu_key = 'surveys'
  AND ump.is_visible = FALSE;

DELETE FROM user_menu_permissions ump
USING users u
WHERE u.id = ump.user_id
  AND lower(coalesce(u.role, '')) = 'personel'
  AND ump.menu_key IN ('survey_manage', 'survey_results')
  AND ump.is_visible = TRUE;

UPDATE unit_menu_profiles
SET is_visible = TRUE,
    source_type = 'overlay_fix',
    note = 'Atanmış anket erişimi için görünür bırakıldı'
WHERE menu_key = 'surveys'
  AND is_visible = FALSE;

COMMIT;
