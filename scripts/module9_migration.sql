ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS automation_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS automation_should_escalate BOOLEAN;
ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS automation_target_team VARCHAR(100);
ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS automation_urgency_level VARCHAR(50);
ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS automation_decision JSONB;
ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS automation_slack_delivery JSONB;
ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS automation_webhook_delivery JSONB;
ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS automation_error TEXT;