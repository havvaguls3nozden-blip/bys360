BEGIN;

INSERT INTO module_settings_retired_backup (
    source_id,
    module_key,
    setting_key,
    label,
    value_text,
    value_type,
    description,
    is_active,
    updated_by_user_id,
    source_created_at,
    source_updated_at
)
SELECT
    ms.id,
    ms.module_key,
    ms.setting_key,
    ms.label,
    ms.value_text,
    ms.value_type,
    ms.description,
    ms.is_active,
    ms.updated_by_user_id,
    ms.created_at,
    ms.updated_at
FROM module_settings ms
WHERE ms.module_key NOT IN (
    'performance_core',
    'performance_scoring',
    'performance_flow',
    'performance_period',
    'performance_feedback',
    'leave_delegation',
    'mail_automation'
)
ON CONFLICT (source_id) DO NOTHING;

DELETE FROM module_settings
WHERE module_key NOT IN (
    'performance_core',
    'performance_scoring',
    'performance_flow',
    'performance_period',
    'performance_feedback',
    'leave_delegation',
    'mail_automation'
);

COMMIT;

SELECT module_key, COUNT(*) AS row_count
FROM module_settings
GROUP BY module_key
ORDER BY module_key;
