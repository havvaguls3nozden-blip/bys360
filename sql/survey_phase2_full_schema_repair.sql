BEGIN;

-- Survey questions: phase 2 columns
ALTER TABLE IF EXISTS survey_questions
    ADD COLUMN IF NOT EXISTS helper_text TEXT,
    ADD COLUMN IF NOT EXISTS logic_mode VARCHAR(20) DEFAULT 'always',
    ADD COLUMN IF NOT EXISTS logic_source_question_id INTEGER,
    ADD COLUMN IF NOT EXISTS logic_operator VARCHAR(30),
    ADD COLUMN IF NOT EXISTS logic_value VARCHAR(255);

UPDATE survey_questions
SET logic_mode = 'always'
WHERE logic_mode IS NULL;

ALTER TABLE IF EXISTS survey_questions
    ALTER COLUMN logic_mode SET DEFAULT 'always';

CREATE INDEX IF NOT EXISTS ix_survey_questions_logic_mode
    ON survey_questions (logic_mode);
CREATE INDEX IF NOT EXISTS ix_survey_questions_logic_source_question_id
    ON survey_questions (logic_source_question_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_survey_questions_logic_source_question'
    ) THEN
        ALTER TABLE survey_questions
            ADD CONSTRAINT fk_survey_questions_logic_source_question
            FOREIGN KEY (logic_source_question_id)
            REFERENCES survey_questions (id)
            ON DELETE SET NULL;
    END IF;
EXCEPTION WHEN duplicate_object THEN
    NULL;
END $$;

-- Survey responses: phase 2 columns
ALTER TABLE IF EXISTS survey_responses
    ADD COLUMN IF NOT EXISTS started_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_saved_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS progress_percent DOUBLE PRECISION DEFAULT 0;

UPDATE survey_responses
SET progress_percent = 0
WHERE progress_percent IS NULL;

ALTER TABLE IF EXISTS survey_responses
    ALTER COLUMN progress_percent SET DEFAULT 0;

CREATE INDEX IF NOT EXISTS ix_survey_responses_started_at
    ON survey_responses (started_at);
CREATE INDEX IF NOT EXISTS ix_survey_responses_last_saved_at
    ON survey_responses (last_saved_at);

COMMIT;
