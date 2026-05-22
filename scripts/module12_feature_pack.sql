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