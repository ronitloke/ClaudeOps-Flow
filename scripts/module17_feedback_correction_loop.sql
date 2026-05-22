ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS user_priority_correct BOOLEAN;

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS corrected_priority VARCHAR(50);

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS user_intent_correct BOOLEAN;

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS corrected_intent VARCHAR(100);

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS user_recommended_action_correct BOOLEAN;

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS corrected_recommended_action TEXT;

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS correction_applied_by VARCHAR(100);

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS correction_source VARCHAR(50);

ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS correction_json JSON;