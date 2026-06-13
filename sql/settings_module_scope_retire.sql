BEGIN;

CREATE TABLE IF NOT EXISTS module_settings_retired_backup (
    backup_id BIGSERIAL PRIMARY KEY,
    archived_at TIMESTAMP NOT NULL DEFAULT NOW(),
    source_id INTEGER NOT NULL,
    module_key VARCHAR(60) NOT NULL,
    setting_key VARCHAR(120) NOT NULL,
    label VARCHAR(150) NOT NULL,
    value_text TEXT NULL,
    value_type VARCHAR(20) NOT NULL,
    description TEXT NULL,
    is_active BOOLEAN NOT NULL,
    updated_by_user_id INTEGER NULL,
    source_created_at TIMESTAMP NULL,
    source_updated_at TIMESTAMP NULL,
    CONSTRAINT uq_module_settings_retired_source UNIQUE (source_id)
);

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

DO $$
DECLARE
    retired_count INTEGER := 0;
BEGIN
    UPDATE module_settings
       SET is_active = FALSE,
           updated_at = NOW()
     WHERE module_key NOT IN (
        'performance_core',
        'performance_scoring',
        'performance_flow',
        'performance_period',
        'performance_feedback',
        'leave_delegation',
        'mail_automation'
     )
       AND is_active IS DISTINCT FROM FALSE;

    GET DIAGNOSTICS retired_count = ROW_COUNT;

    IF retired_count > 0 AND EXISTS (
        SELECT 1
          FROM information_schema.tables
         WHERE table_schema = 'public'
           AND table_name = 'settings_change_logs'
    ) THEN
        INSERT INTO settings_change_logs (
            actor_user_id,
            target_user_id,
            target_role_name,
            target_unit_name,
            change_scope,
            action_type,
            summary,
            previous_state_json,
            new_state_json,
            reverted_from_log_id,
            is_rollback,
            created_at,
            updated_at
        )
        VALUES (
            NULL,
            NULL,
            NULL,
            NULL,
            'module_settings',
            'cleanup',
            'Canlı kapsam dışı modül ayarları pasife alındı',
            NULL,
            json_build_object(
                'retired_count', retired_count,
                'retired_module_keys', (
                    SELECT COALESCE(json_agg(DISTINCT module_key ORDER BY module_key), '[]'::json)
                      FROM module_settings
                     WHERE module_key NOT IN (
                        'performance_core',
                        'performance_scoring',
                        'performance_flow',
                        'performance_period',
                        'performance_feedback',
                        'leave_delegation',
                        'mail_automation'
                     )
                )
            )::text,
            NULL,
            FALSE,
            NOW(),
            NOW()
        );
    END IF;
END $$;

COMMIT;

-- Kontrol sorgusu
SELECT module_key, COUNT(*) AS row_count, BOOL_OR(is_active) AS any_active
FROM module_settings
GROUP BY module_key
ORDER BY module_key;
