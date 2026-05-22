ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS automation_zapier_delivery JSONB;
ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS automation_make_delivery JSONB;
ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS automation_ready BOOLEAN DEFAULT FALSE;