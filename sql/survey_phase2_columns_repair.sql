BEGIN;

ALTER TABLE survey_questions
    ADD COLUMN IF NOT EXISTS helper_text TEXT;

ALTER TABLE survey_questions
    ADD COLUMN IF NOT EXISTS logic_mode VARCHAR(20) NOT NULL DEFAULT 'always';

ALTER TABLE survey_questions
    ADD COLUMN IF NOT EXISTS logic_source_question_id INTEGER;

ALTER TABLE survey_questions
    ADD COLUMN IF NOT EXISTS logic_operator VARCHAR(30);

ALTER TABLE survey_questions
    ADD COLUMN IF NOT EXISTS logic_value VARCHAR(255);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_survey_questions_logic_source_question'
    ) THEN
        ALTER TABLE survey_questions
            ADD CONSTRAINT fk_survey_questions_logic_source_question
            FOREIGN KEY (logic_source_question_id)
            REFERENCES survey_questions(id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_survey_questions_logic_source_question_id
    ON survey_questions (logic_source_question_id);

ALTER TABLE survey_responses
    ADD COLUMN IF NOT EXISTS started_at TIMESTAMP NULL;

ALTER TABLE survey_responses
    ADD COLUMN IF NOT EXISTS last_saved_at TIMESTAMP NULL;

ALTER TABLE survey_responses
    ADD COLUMN IF NOT EXISTS progress_percent INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS ix_survey_responses_started_at
    ON survey_responses (started_at);

CREATE INDEX IF NOT EXISTS ix_survey_responses_last_saved_at
    ON survey_responses (last_saved_at);

UPDATE survey_questions
SET logic_mode = 'always'
WHERE logic_mode IS NULL;

UPDATE survey_responses
SET progress_percent = 0
WHERE progress_percent IS NULL;

COMMIT;
