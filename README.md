# ClaudeOps Flow

ClaudeOps Flow is an AI-powered support ticket triage and workflow automation platform. It converts unstructured support tickets into structured operational outputs, detects SLA-risk cases, recommends next actions, stores workflow history in PostgreSQL, and prepares downstream automation payloads for Zapier, Make, Gmail, Trello, Google Sheets, Slack, or generic webhooks.

## Features

- AI ticket triage using Claude, Gemini, or Groq
- Queue, priority, type, intent, and language prediction
- SLA-risk and human-review detection
- Structured field extraction
- Draft customer response generation
- PostgreSQL logging and audit trail
- Approval queue before executing critical automation
- Zapier and Make webhook integration
- Gmail, Trello, and Google Sheets downstream-ready payloads
- Benchmark runner for queue consistency and latency
- Streamlit dashboard with admin and analyst roles
- Docker support for API, dashboard, and PostgreSQL

## Tech Stack

- Python
- FastAPI
- Streamlit
- PostgreSQL
- SQLAlchemy
- Pydantic
- Anthropic Claude API
- Gemini API
- Groq API
- Zapier Webhooks
- Make Webhooks
- Docker

## Project Architecture

```text
Support Ticket
     |
     v
FastAPI Triage Endpoint
     |
     v
LLM JSON Triage
     |
     v
Validation + Normalization
     |
     v
PostgreSQL Log
     |
     v
Automation Decision
     |
     +---- If high-risk: Approval Queue
     |
     +---- If approved: Zapier / Make / Webhook
     |
     v
Streamlit Dashboard
