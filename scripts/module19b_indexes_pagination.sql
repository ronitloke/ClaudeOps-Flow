-- Module 19B: Database indexes for dashboard, approval queue, observability, and audit reads

-- Optional but useful for faster subject/request_id search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Triage logs: common dashboard filters
CREATE INDEX IF NOT EXISTS ix_triage_logs_created_at_desc
ON triage_logs(created_at DESC);

CREATE INDEX IF NOT EXISTS ix_triage_logs_status_created_at
ON triage_logs(status, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_triage_logs_queue_created_at
ON triage_logs(predicted_queue, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_triage_logs_priority_created_at
ON triage_logs(predicted_priority, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_triage_logs_status_queue_priority_created_at
ON triage_logs(status, predicted_queue, predicted_priority, created_at DESC);

-- Approval queue: pending approvals
CREATE INDEX IF NOT EXISTS ix_triage_logs_approval_status_created_at
ON triage_logs(approval_status, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_triage_logs_approval_required_status_created_at
ON triage_logs(approval_required, approval_status, created_at DESC);

-- Request detail lookup
CREATE INDEX IF NOT EXISTS ix_triage_logs_request_id_lookup
ON triage_logs(request_id);

-- Text search acceleration for dashboard search
CREATE INDEX IF NOT EXISTS ix_triage_logs_subject_trgm
ON triage_logs USING gin (lower(subject) gin_trgm_ops);

CREATE INDEX IF NOT EXISTS ix_triage_logs_request_id_trgm
ON triage_logs USING gin (lower(request_id) gin_trgm_ops);

-- Benchmark history
CREATE INDEX IF NOT EXISTS ix_benchmark_runs_created_at_desc
ON benchmark_runs(created_at DESC);

-- Policy audit table
CREATE INDEX IF NOT EXISTS ix_outbound_action_audits_created_at_desc
ON outbound_action_audits(created_at DESC);

CREATE INDEX IF NOT EXISTS ix_outbound_action_audits_actor_role_created_at
ON outbound_action_audits(actor_role, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_outbound_action_audits_decision_created_at
ON outbound_action_audits(decision, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_outbound_action_audits_action_decision_created_at
ON outbound_action_audits(action_key, decision, created_at DESC);