# DECISIONS.md

Project: PrivacyProtector — MVP decisions (finalized)

1. Backend stack: **Python 3.11+, FastAPI** + Uvicorn. Use SQLModel (SQLAlchemy) for ORM + Alembic for migrations.
2. Frontend: React (Next.js optional) — separate repo folder `frontend/`.
3. LLM provider: OpenAI ChatGPT API (planner + remediation). Calls are made from backend only.
4. Search provider: **Bing Web Search API** for `searchWeb` (with local mock mode).
5. Social sources (MVP): **GitHub** (public profile API) and **Reddit** (public posts API).
6. Paid enrichment: **Excluded** from MVP (enrichEntity omitted / stubbed).
7. Data store: **Postgres** via Docker Compose for dev; optionally local SQLCipher for Electron local-first later.
8. MCP: backend will expose a tool registry and tool-call endpoints conforming to our MCP-like JSON tool schema (tools: searchWeb, searchSocial, checkBreach, reverseImageSearch (mock), scoreRisk, generateRemediation).
9. Evals: Use OpenAI Evals for automated tests. CI will run smoke evals using mocked connectors if `OPENAI_API_KEY` is missing.
10. Security: Local-first default, pseudonymize identifiers before sending to LLM (unless user explicitly opts-in), no face recognition, store audit logs signed (JWS).
11. Devops: Docker Compose for local development. CI: GitHub Actions with lint / tests / smoke-evals.
