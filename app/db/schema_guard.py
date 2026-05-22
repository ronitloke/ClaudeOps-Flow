from sqlalchemy import text

from app.db.database import engine


REQUIRED_TRIAGE_LOG_COLUMNS = {
    "approval_required",
    "approval_status",
    "approval_reason",
    "approved_by",
    "approved_at",
    "rejected_by",
    "rejected_at",
    "automation_executed",
    "automation_executed_at",
    "prompt_version",
    "model_version",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "estimated_cost_usd",
    "trace_json",
    "user_queue_correct",
    "corrected_queue",
    "user_priority_correct",
    "corrected_priority",
    "user_intent_correct",
    "corrected_intent",
    "user_recommended_action_correct",
    "corrected_recommended_action",
    "user_feedback_notes",
    "correction_applied_by",
    "correction_source",
    "correction_json",
    "feedback_at",
}


def ensure_runtime_schema() -> None:
    """
    Dev/demo schema guard.

    This runs inside the FastAPI container using the same SQLAlchemy engine
    used by the live API routes. It prevents old local tables from breaking
    newer code when columns were added module by module.
    """

    alter_sql = """
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS approval_required BOOLEAN NOT NULL DEFAULT FALSE;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS approval_status VARCHAR(30) NOT NULL DEFAULT 'not_required';
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS approval_reason TEXT;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS approved_by VARCHAR(120);
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS rejected_by VARCHAR(120);
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMPTZ;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS automation_executed BOOLEAN NOT NULL DEFAULT FALSE;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS automation_executed_at TIMESTAMPTZ;

    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS prompt_version VARCHAR(120);
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS model_version VARCHAR(120);
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS input_tokens INTEGER DEFAULT 0;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS output_tokens INTEGER DEFAULT 0;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS total_tokens INTEGER DEFAULT 0;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS estimated_cost_usd FLOAT DEFAULT 0;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS trace_json JSON;

    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS user_queue_correct BOOLEAN;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS corrected_queue VARCHAR(120);
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS user_priority_correct BOOLEAN;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS corrected_priority VARCHAR(50);
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS user_intent_correct BOOLEAN;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS corrected_intent VARCHAR(120);
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS user_recommended_action_correct BOOLEAN;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS corrected_recommended_action TEXT;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS user_feedback_notes TEXT;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS correction_applied_by VARCHAR(120);
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS correction_source VARCHAR(80);
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS correction_json JSON;
    ALTER TABLE triage_logs ADD COLUMN IF NOT EXISTS feedback_at TIMESTAMPTZ;
    """

    verify_sql = """
    SELECT a.attname
    FROM pg_attribute a
    JOIN pg_class c ON a.attrelid = c.oid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.oid = 'triage_logs'::regclass
      AND a.attname = ANY(:columns)
      AND a.attnum > 0
      AND NOT a.attisdropped;
    """

    with engine.begin() as conn:
        db_info = conn.execute(
            text(
                """
                SELECT 
                    current_database() AS database_name,
                    current_schema() AS schema_name,
                    current_setting('search_path') AS search_path,
                    'triage_logs'::regclass::text AS resolved_table;
                """
            )
        ).mappings().one()

        print("RUNTIME DB INFO:", dict(db_info))

        for statement in alter_sql.strip().split(";"):
            if statement.strip():
                conn.execute(text(statement))

        found_rows = conn.execute(
            text(verify_sql),
            {"columns": list(REQUIRED_TRIAGE_LOG_COLUMNS)},
        ).fetchall()

        found_columns = {row[0] for row in found_rows}
        missing_columns = sorted(REQUIRED_TRIAGE_LOG_COLUMNS - found_columns)

        if missing_columns:
            raise RuntimeError(
                f"Runtime schema check failed. Missing triage_logs columns: {missing_columns}"
            )

        print("Runtime schema check OK for triage_logs.")