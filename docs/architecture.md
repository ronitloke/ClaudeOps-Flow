# ClaudeOps Flow Architecture

ClaudeOps Flow is built as a full-stack AI operations workflow platform.

## Components

### Streamlit Frontend

The frontend provides:

- role-based login
- ticket submission
- operations dashboard
- approval queue
- integrations and benchmark section
- observability and evaluation section
- project overview

### FastAPI Backend

The backend provides REST APIs for:

- ticket triage
- approval queue
- policy audit
- benchmark execution
- observability summary
- workflow contract publishing
- correction feedback

### PostgreSQL

PostgreSQL stores:

- triage request logs
- raw request payloads
- raw LLM outputs
- structured predictions
- automation decisions
- approval records
- policy audit rows
- benchmark history
- feedback corrections

### LLM Triage Layer

The LLM layer converts support ticket text into structured operational fields:

- queue
- priority
- intent
- summary
- recommended action
- SLA risk
- confidence
- draft response

### Policy and Approval Layer

The policy and approval layer ensures sensitive external automation does not run without governance.

Critical workflows can require human approval before external delivery.

### Automation Contract Layer

The outbound automation contract prepares predictable JSON payloads for workflow systems such as Zapier, Make, Slack, or generic webhooks.
