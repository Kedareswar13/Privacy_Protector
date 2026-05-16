# DECISIONS.md

Project: PrivacyProtector — MVP decisions (finalized)

1. Backend stack: **Python 3.11+, FastAPI** + Uvicorn. Use SQLModel (SQLAlchemy) for ORM.
2. Frontend: **Next.js 14** with TailwindCSS — in `frontend/` directory.
3. LLM provider: **Ollama** (local, qwen3.5:latest). All inference runs locally — no cloud LLM dependency.
4. Search provider: **Serper.dev** (Google Search API) for `searchWeb`.
5. Social sources (MVP): GitHub and Reddit APIs — **stubbed** until API keys are configured.
6. Paid enrichment: **Excluded** from MVP (enrichEntity omitted / stubbed).
7. Data store: **SQLite** for local dev (fallback), optionally **PostgreSQL** for production.
8. MCP: backend exposes a tool registry and tool-call endpoints conforming to MCP-like JSON tool schema (tools: searchWeb, searchSocial, checkBreach, reverseImageSearch, scoreRisk, classifyItems, generateRemediation).
9. Chat interface: Primary user interaction is via a **conversational chat** on `/dashboard`. Backend routes between general Q&A (Ollama) and web search (Serper + Ollama classification) based on intent detection.
10. Security: Local-first default, pseudonymize identifiers before sending to LLM (unless user explicitly opts-in), no face recognition, JWT-based auth.
11. Devops: Manual local setup. Backend and frontend run as separate dev servers.
