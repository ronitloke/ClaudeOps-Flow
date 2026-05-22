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
    delivery_json JSON,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_outbound_action_audits_request_id
ON outbound_action_audits(request_id);

CREATE INDEX IF NOT EXISTS ix_outbound_action_audits_created_at
ON outbound_action_audits(created_at);

CREATE INDEX IF NOT EXISTS ix_outbound_action_audits_action_key
ON outbound_action_audits(action_key);