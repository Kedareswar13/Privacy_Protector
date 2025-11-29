# docs/architecture.md

PrivacyProtector — Architecture (MVP, Python/FastAPI, MCP)

## Overview
- Web-based, agentic platform.
- FastAPI backend exposes REST + MCP tool endpoints.
- LLM Planner (ChatGPT) is used as the decision-making agent: it returns a JSON plan listing MCP tool calls.
- Executor runs tool calls, enforces safety & pseudonymization, writes results to DB.
- EVALS run in CI for discovery, risk classification, remediation quality, and agenticity metrics.

## Components

### 1. Frontend (React)
- Consent UI, seed input, scan progress, risk dashboard, item detail, remediation composer.

### 2. Backend (FastAPI)
- /auth endpoints (JWT)
- /consent endpoints (sign & store)
- /scan endpoints (start, status, items)
- /planner endpoints (planner wrapper debug)
- /mcp/tools (registry)
- /mcp/call (executor endpoint; internal)

### 3. MCP tool implementations (server-side)
- searchWeb (Bing)
- searchSocial (GitHub, Reddit)
- checkBreach (HaveIBeenPwned or mock)
- reverseImageSearch (mocked for MVP)
- scoreRisk (local rules)
- generateRemediation (LLM handler with pseudonymization)

### 4. State store
- Postgres DB holds users, consents, scans, items, pseudonym_map, tool_calls, audit_log.

### 5. LLM interactions
- Planner: calls ChatGPT to produce JSON plan (strategy + tool selection + rationale).
- Remediation: ChatGPT drafts pseudonymized emails/steps.
- All LLM requests made only from backend. PII is pseudonymized before sending.

### 6. Evals
- OpenAI Evals harness invoked in CI.
- Local mock-run mode available when no keys are present.

## Data flow (high level)
User → Frontend → Backend (create scan) → Planner (LLM) returns plan → Executor calls MCP tools → Tools return results → Executor updates state → Loop until planner stop → Final Report (LLM) → User.

## Security & privacy
- Pseudonymize identifiers prior to OpenAI calls by default.
- Consent must be explicit; store signed audit entries.
- No face-recognition; reverse image search allowed only as a metadata lookup.
