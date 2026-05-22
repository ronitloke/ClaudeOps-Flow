from sqlalchemy import text

from app.db.database import engine


SCHEMA_SQL = """
ALTER TABLE triage_logs
ADD COLUMN IF NOT EXISTS latency_ms DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS had_retry BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS error_type VARCHAR(100),

ADD COLUMN IF NOT EXISTS automation_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS automation_ready BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS automation_should_escalate BOOLEAN,
ADD COLUMN IF NOT EXISTS automation_target_team VARCHAR(100),
ADD COLUMN IF NOT EXISTS automation_urgency_level VARCHAR(50),
ADD COLUMN IF NOT EXISTS automation_decision JSONB,
ADD COLUMN IF NOT EXISTS automation_slack_delivery JSONB,
ADD COLUMN IF NOT EXISTS automation_webhook_delivery JSONB,
ADD COLUMN IF NOT EXISTS automation_zapier_delivery JSONB,
ADD COLUMN IF NOT EXISTS automation_make_delivery JSONB,
ADD COLUMN IF NOT EXISTS automation_error TEXT,

ADD COLUMN IF NOT EXISTS approval_required BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS approval_status VARCHAR(30) NOT NULL DEFAULT 'not_required',
ADD COLUMN IF NOT EXISTS approval_reason TEXT,
ADD COLUMN IF NOT EXISTS approved_by VARCHAR(120),
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS rejected_by VARCHAR(120),
ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS automation_executed BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS automation_executed_at TIMESTAMPTZ,

ADD COLUMN IF NOT EXISTS prompt_version VARCHAR(120),
ADD COLUMN IF NOT EXISTS model_version VARCHAR(120),
ADD COLUMN IF NOT EXISTS input_tokens INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS output_tokens INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_tokens INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS estimated_cost_usd DOUBLE PRECISION DEFAULT 0,
ADD COLUMN IF NOT EXISTS trace_json JSONB,

ADD COLUMN IF NOT EXISTS user_queue_correct BOOLEAN,
ADD COLUMN IF NOT EXISTS corrected_queue VARCHAR(150),
ADD COLUMN IF NOT EXISTS user_priority_correct BOOLEAN,
ADD COLUMN IF NOT EXISTS corrected_priority VARCHAR(80),
ADD COLUMN IF NOT EXISTS user_intent_correct BOOLEAN,
ADD COLUMN IF NOT EXISTS corrected_intent VARCHAR(150),
ADD COLUMN IF NOT EXISTS user_recommended_action_correct BOOLEAN,
ADD COLUMN IF NOT EXISTS corrected_recommended_action TEXT,
ADD COLUMN IF NOT EXISTS user_feedback_notes TEXT,
ADD COLUMN IF NOT EXISTS correction_applied_by VARCHAR(100),
ADD COLUMN IF NOT EXISTS correction_source VARCHAR(100),
ADD COLUMN IF NOT EXISTS correction_json JSONB,
ADD COLUMN IF NOT EXISTS feedback_at TIMESTAMPTZ;
"""

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS benchmark_runs (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    sample_size INTEGER NOT NULL,
    success_count INTEGER NOT NULL,
    failure_count INTEGER NOT NULL,
    queue_match_count INTEGER NOT NULL,
    queue_prediction_consistency_pct DOUBLE PRECISION NOT NULL,
    average_latency_ms DOUBLE PRECISION,
    escalated_count INTEGER NOT NULL,
    successful_automation_ready_outputs INTEGER NOT NULL,
    run_config JSONB,
    results_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS outbound_action_audits (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(36) NOT NULL,
    log_id INTEGER,
    actor VARCHAR(100),
    actor_role VARCHAR(50),
    action_key VARCHAR(100) NOT NULL,
    channel VARCHAR(100),
    decision VARCHAR(30) NOT NULL,
    policy_rule VARCHAR(150),
    reason TEXT,
    queue VARCHAR(100),
    priority VARCHAR(50),
    delivery_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

INDEX_SQL = """
CREATE INDEX IF NOT EXISTS ix_triage_logs_created_at_desc
ON triage_logs(created_at DESC);

CREATE INDEX IF NOT EXISTS ix_triage_logs_request_id_lookup
ON triage_logs(request_id);

CREATE INDEX IF NOT EXISTS ix_triage_logs_status_created_at
ON triage_logs(status, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_triage_logs_queue_created_at
ON triage_logs(predicted_queue, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_triage_logs_priority_created_at
ON triage_logs(predicted_priority, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_triage_logs_approval_required_status_created_at
ON triage_logs(approval_required, approval_status, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_benchmark_runs_created_at_desc
ON benchmark_runs(created_at DESC);

CREATE INDEX IF NOT EXISTS ix_outbound_action_audits_created_at_desc
ON outbound_action_audits(created_at DESC);

CREATE INDEX IF NOT EXISTS ix_outbound_action_audits_request_id
ON outbound_action_audits(request_id);
"""


def main() -> None:
    with engine.begin() as conn:
        db_info = conn.execute(
            text("SELECT current_database(), current_schema();")
        ).fetchone()

        print("Connected DB/schema used by API:", db_info)

        conn.execute(text(SCHEMA_SQL))
        conn.execute(text(TABLE_SQL))
        conn.execute(text(INDEX_SQL))

        columns = conn.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'triage_logs'
                AND column_name IN (
                    'approval_required',
                    'approval_status',
                    'trace_json',
                    'user_priority_correct',
                    'corrected_recommended_action'
                )
                ORDER BY column_name;
                """
            )
        ).fetchall()

        print("Verified columns:")
        for col in columns:
            print("-", col[0])

    print("Schema fix completed successfully.")


if __name__ == "__main__":
    main()  