BEGIN;

ALTER TABLE IF EXISTS survey_questions
    ADD COLUMN IF NOT EXISTS helper_text TEXT,
    ADD COLUMN IF NOT EXISTS logic_mode VARCHAR(50),
    ADD COLUMN IF NOT EXISTS logic_source_question_id INTEGER,
    ADD COLUMN IF NOT EXISTS logic_operator VARCHAR(50),
    ADD COLUMN IF NOT EXISTS logic_value TEXT;

UPDATE survey_questions SET logic_mode = COALESCE(logic_mode, 'always');
UPDATE survey_questions SET logic_operator = COALESCE(logic_operator, 'answered');

ALTER TABLE IF EXISTS survey_responses
    ADD COLUMN IF NOT EXISTS started_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_saved_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS progress_percent INTEGER;

UPDATE survey_responses
SET started_at = COALESCE(started_at, created_at, submitted_at),
    last_saved_at = COALESCE(last_saved_at, updated_at, submitted_at, created_at),
    progress_percent = COALESCE(progress_percent, CASE WHEN is_completed THEN 100 ELSE 0 END);

CREATE INDEX IF NOT EXISTS ix_survey_responses_survey_completed
    ON survey_responses (survey_id, is_completed);

CREATE INDEX IF NOT EXISTS ix_survey_questions_survey_sort
    ON survey_questions (survey_id, sort_order, id);

COMMIT;
