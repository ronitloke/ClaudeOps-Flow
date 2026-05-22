ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS prompt_version VARCHAR(80);

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS model_version VARCHAR(120);

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS input_tokens INTEGER;

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS output_tokens INTEGER;

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS total_tokens INTEGER;

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS estimated_cost_usd FLOAT;

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS trace_json JSON;

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS user_queue_correct BOOLEAN;

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS corrected_queue VARCHAR(100);

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS user_feedback_notes TEXT;

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS feedback_at TIMESTAMPTZ;