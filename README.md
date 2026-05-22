# ClaudeOps Flow

ClaudeOps Flow is a full-stack AI operations workflow platform that converts unstructured support tickets into structured triage decisions, escalation recommendations, human approval workflows, automation-ready payloads, benchmark analytics, and observability insights.

The project demonstrates how an AI-powered support operations system can be designed with production-style thinking: role-based access, deterministic routing, human approval gates, policy-based automation control, PostgreSQL logging, benchmark history, correction feedback, and monitoring dashboards.

---

## Preview

### Login & Workspace Selection / Live Ticket Submission
<img src="docs/Screenshots/Frontend/1.%20Login%20Page.png" style="width: 48%; height: 280px; object-fit: cover;" alt="Login Workspace"> <img src="docs/Screenshots/Frontend/2.%20Submit%20Ticket.png" style="width: 48%; height: 280px; object-fit: cover;" alt="Submit Ticket">

### Operations Dashboard / Human Approval Queue
<img src="docs/Screenshots/Frontend/3.%20Operations%20Dashboard.png" style="width: 48%; height: 280px; object-fit: cover;" alt="Operations Dashboard"> <img src="docs/Screenshots/Frontend/4.%20Approval%20Queue.png" style="width: 48%; height: 280px; object-fit: cover;" alt="Approval Queue">

### Integrations & Benchmark / Project Overview
<img src="docs/Screenshots/Frontend/5.%20Integrations%20%26%20Benchmark.png" style="width: 48%; height: 280px; object-fit: cover;" alt="Integrations Benchmark"> <img src="docs/Screenshots/Frontend/7.%20Project%20Overview.png" style="width: 48%; height: 280px; object-fit: cover;" alt="Project Overview">



---

## What This Project Does

ClaudeOps Flow takes a support ticket and performs an end-to-end AI operations workflow:

1. Accepts a support ticket from the Streamlit frontend.
2. Sends the request to a FastAPI backend.
3. Runs AI triage using an LLM provider.
4. Predicts queue, priority, intent, SLA risk, summary, and recommended action.
5. Stores request, response, latency, retry data, and metadata in PostgreSQL.
6. Applies automation decision logic.
7. Routes critical automation plans into a human approval queue.
8. Applies policy-based checks before external automation.
9. Prepares Zapier, Make, Slack, and generic webhook-ready payloads.
10. Tracks benchmark performance, observability, feedback corrections, and policy audit history.

---

## Key Features

### AI Ticket Triage

- Predicts support queue
- Predicts ticket priority
- Detects likely user intent
- Detects SLA risk
- Generates ticket summary
- Generates recommended action
- Optionally generates a draft customer response

### Deterministic Routing

- Uses rule-based routing before LLM handling
- Supports specialist routing profiles
- Improves consistency and explainability
- Reduces dependency on one generic prompt

### Human Approval Queue

- Critical automation plans wait for approval
- Admin or Ops Analyst can approve/reject controlled actions
- Approval result is stored and visible in the dashboard
- Prevents automatic execution of sensitive workflows

### Policy-Based Automation Control

- Applies governance rules before outbound automation
- Tracks allowed and blocked external actions
- Supports least-privilege automation design
- Records policy audit history

### Integrations

- Zapier-ready webhook payloads
- Make-ready webhook payloads
- Slack/webhook-style contract design
- Stable outbound automation contract

### Benchmarking

- Runs benchmark samples
- Tracks queue consistency
- Tracks priority distribution
- Tracks escalation count
- Tracks latency distribution
- Stores benchmark history in PostgreSQL

### Observability

- Tracks latency
- Tracks errors
- Tracks retry counts
- Tracks token usage
- Tracks estimated cost
- Tracks low-confidence outputs
- Tracks correction feedback
- Tracks policy audit records
- Shows raw JSON traces for debugging

### Role-Based Frontend

Two demo workspaces are supported:

| Role | Access |
|---|---|
| Admin | Full access to submission, dashboard, approvals, integrations, benchmark, observability, and project overview |
| Ops Analyst | Access to ticket submission, operations dashboard, approval queue, and project overview |

---

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- LLM API integration
- Policy engine
- REST APIs

### Frontend

- Streamlit
- Custom HTML/CSS
- Altair charts
- Pandas dataframes
- Role-based UI rendering

### Infrastructure

- Docker
- Docker Compose
- PostgreSQL container
- API container
- Streamlit container

---

## Architecture

```text
User
 │
 ▼
Streamlit Frontend
 │
 │  Submit ticket / view dashboards / approve automation
 ▼
FastAPI Backend
 │
 ├── AI triage service
 ├── Deterministic routing
 ├── Automation decision service
 ├── Approval service
 ├── Policy engine
 ├── Benchmark service
 └── Observability service
 │
 ▼
PostgreSQL
 │
 ├── triage logs
 ├── automation decisions
 ├── approvals
 ├── policy audit
 ├── benchmark runs
 ├── feedback corrections
 └── observability traces
 │
 ▼
Optional external automation
 │
 ├── Zapier
 ├── Make
 ├── Slack
 └── Generic webhooks
