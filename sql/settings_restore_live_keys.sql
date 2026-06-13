-- BYS360 settings recovery: keep live performance and communication-related setting groups active
BEGIN;

UPDATE module_settings
SET is_active = TRUE
WHERE module_key IN (
    'leave_delegation',
    'mail_automation',
    'performance_core',
    'performance_feedback',
    'performance_flow',
    'performance_period',
    'performance_scoring'
);

COMMIT;
