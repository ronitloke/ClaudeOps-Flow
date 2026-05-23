# ClaudeOps Flow

ClaudeOps Flow is a full-stack AI operations workflow platform that converts unstructured support tickets into structured triage decisions, escalation recommendations, human approval workflows, automation-ready payloads, benchmark analytics, and observability insights.

The project demonstrates how an AI-powered support operations system can be designed with production-style thinking: role-based access, deterministic routing, human approval gates, policy-based automation control, PostgreSQL logging, benchmark history, correction feedback, and monitoring dashboards.

---

## Preview

### Login & Workspace Selection & Live Ticket Submission
<img src="docs/Screenshots/Frontend/1.%20Login%20Page.png" style="width: 48%; height: 300px; object-fit: contain; background: #f6f8fa;" alt="Login Workspace"> <img src="docs/Screenshots/Frontend/2.%20Submit%20Ticket.png" style="width: 48%; height: 300px; object-fit: contain; background: #f6f8fa;" alt="Submit Ticket">

### Operations Dashboard & Human Approval Queue
<img src="docs/Screenshots/Frontend/3.%20Operations%20Dashboard.png" style="width: 48%; height: 300px; object-fit: contain; background: #f6f8fa;" alt="Operations Dashboard"> <img src="docs/Screenshots/Frontend/4.%20Approval%20Queue.png" style="width: 48%; height: 300px; object-fit: contain; background: #f6f8fa;" alt="Approval Queue">

### Integrations & Benchmark & Project Overview
<img src="docs/Screenshots/Frontend/5.%20Integrations%20%26%20Benchmark.png" style="width: 48%; height: 300px; object-fit: contain; background: #f6f8fa;" alt="Integrations Benchmark"> <img src="docs/Screenshots/Frontend/7.%20Project%20Overview.png" style="width: 48%; height: 300px; object-fit: contain; background: #f6f8fa;" alt="Project Overview">


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

```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ClaudeOps-Flow.git
cd ClaudeOps-Flow
```

### 2. Create environment file

```bash
cp .env.example .env
```

On Windows PowerShell:

```bash
copy .env.example .env
```

Update .env with your local values.

### Run with Docker

This is the recommended way.

```bash
docker compose up --build
```

The services should run at:


| Service | URL |
| :--- | :--- |
| Streamlit Frontend | http://localhost:8501 |
| FastAPI Backend | http://localhost:8000 |
| FastAPI Swagger | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |



1. Create virtual environment

```bash
python -m venv .venv
```

Activate it:

Windows PowerShell:

```bash
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

2. Install dependencies
3. 
```bash
pip install -r requirements.txt
```

3. Start FastAPI backend

```bash
uvicorn app.main:app --reload --port 8000
```

4. Start Streamlit frontend

Open another terminal:

```bash
streamlit run streamlit_app.py
```

Then open:

```bash
http://localhost:8501
```

Demo Login

The demo login credentials are configured through .env.

Default example:

Role	Username	Password
Admin	admin	admin123
Ops Analyst	analyst	analyst123
Main Application Pages
Submit Ticket

Used to submit a support ticket and run the AI triage workflow.

Shows:

predicted queue
priority
intent
confidence
SLA risk
latency
retry count
escalation decision
automation approval status
draft response
structured JSON output
Operations Dashboard

Used to monitor stored triage logs.

Shows:

total tickets
success rate
SLA-risk rate
escalation rate
average confidence
average latency
retry rate
top queue
distribution charts
latency trend
recent triage records
detailed request review
Approval Queue

Used to review critical automation plans before external actions are executed.

Shows:

subject
summary
priority
queue
target team
SLA risk
human review flag
approval reason
approve/reject buttons
Integrations & Benchmark

Used to review automation readiness and benchmark the AI workflow.

Shows:

Zapier hook status
Make hook status
outbound workflow contract
benchmark runner
benchmark summary
benchmark charts
benchmark history
Observability & Evaluation

Used to monitor production-style AI system behavior.

Shows:

runtime health
token and cost monitoring
latency/error/low-confidence alerts
correction-aware benchmark analytics
human feedback correction loop
correction analytics
policy-based tool access audit
raw observability JSON
Project Overview

Used to explain the system clearly for GitHub, LinkedIn, and interviews.

Shows:

system overview
processed tickets
success rate
escalation rate
average latency
product capabilities
core workflow
technical architecture
role-based experience
API Overview

FastAPI exposes endpoints for:

```bash
POST /triage/ticket
GET  /config
GET  /contracts/outbound-automation/v1
GET  /approvals/pending
POST /approvals/{request_id}/approve
POST /approvals/{request_id}/reject
POST /benchmark/run
GET  /observability/summary
GET  /benchmark/correction-aware-summary
GET  /policy/audit/recent
POST /triage/logs/{request_id}/feedback
```

Swagger documentation is available at:

```bash
http://localhost:8000/docs
```

Example Workflow
Login as Admin.
Submit a payment failure ticket.
Review the AI triage result.
Check the Operations Dashboard.
Open the Approval Queue.
Approve or reject the automation.
Review policy decisions.
Run a benchmark.
Check Observability metrics.
Review the Project Overview page.
Screenshot Guide

Recommended screenshots for GitHub:

File	Description
01-login-workspace.png	Login page and workspace selector
02-submit-ticket-ai-result.png	Ticket submission and AI result
03-operations-dashboard.png	Operations dashboard with charts and table
04-approval-queue.png	Human approval queue
05-integrations-benchmark.png	Integration readiness and benchmark
06-observability-evaluation.png	Observability and evaluation page
07-project-overview.png	Project overview and architecture
