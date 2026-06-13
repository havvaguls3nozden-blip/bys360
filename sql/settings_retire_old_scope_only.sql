-- BYS360 settings cleanup: retire only old/non-live module groups
BEGIN;

-- Optional backup
CREATE TABLE IF NOT EXISTS module_settings_retired_backup AS
SELECT * FROM module_settings WHERE 1=0;

INSERT INTO module_settings_retired_backup
SELECT *
FROM module_settings
WHERE module_key IN (
    'education',
    'portal',
    'repository',
    'strategy'
)
AND NOT EXISTS (
    SELECT 1
    FROM module_settings_retired_backup b
    WHERE b.id = module_settings.id
);

-- Retire only non-live old groups
UPDATE module_settings
SET is_active = FALSE
WHERE module_key IN (
    'education',
    'portal',
    'repository',
    'strategy'
);

-- Legacy umbrella key:
-- Keep disabled unless current code explicitly uses it.
UPDATE module_settings
SET is_active = FALSE
WHERE module_key = 'performance';

COMMIT;
