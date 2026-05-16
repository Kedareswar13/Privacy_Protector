# PrivacyProtector — Architecture

## Overview

PrivacyProtector is an AI-powered privacy scanner that helps users discover where
their personal data appears on the public internet. It uses a **chat-based interface**
where users can ask general privacy questions or request web searches for their
digital footprint.

**Key design choices:**
- **Local-first AI** — all LLM inference runs on the user's machine via **Ollama** (no data sent to OpenAI/cloud LLMs).
- **Serper API** for real-time web search (Google Search results via serper.dev).
- **Intent-based routing** — the backend detects whether the user wants a general answer or a web search and routes accordingly.
- **MCP-style tool registry** — tools are registered with JSON schemas and can be called individually or orchestrated by the planner.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     User's Browser                           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │           Next.js Frontend (port 3000)                 │  │
│  │  • Login / Register page                               │  │
│  │  • Chat Dashboard (privacy assistant)                  │  │
│  │  • Scan detail pages                                   │  │
│  └────────────────────┬───────────────────────────────────┘  │
└───────────────────────┼──────────────────────────────────────┘
                        │ REST API calls
                        ▼
┌──────────────────────────────────────────────────────────────┐
│              FastAPI Backend (port 8000)                      │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ /auth    │  │ /chat    │  │ /scans   │  │ /mcp     │    │
│  │ (JWT)    │  │ (main)   │  │ (scans)  │  │ (tools)  │    │
│  └──────────┘  └─────┬────┘  └──────────┘  └──────────┘    │
│                      │                                       │
│         ┌────────────┴────────────┐                          │
│         │    Intent Detection     │                          │
│         └─────┬──────────┬────────┘                          │
│               │          │                                   │
│     General   │          │  Search                           │
│     Question  │          │  Request                          │
│               ▼          ▼                                   │
│         ┌──────────┐  ┌──────────────┐                      │
│         │ Ollama   │  │ Serper API   │                      │
│         │ (local)  │  │ (web search) │                      │
│         └──────────┘  └──────┬───────┘                      │
│                              │                               │
│                              ▼                               │
│                        ┌───────────┐                         │
│                        │ Classify  │ ← Ollama risk scoring   │
│                        │ & Score   │                         │
│                        └───────────┘                         │
│                              │                               │
│                              ▼                               │
│                     ┌────────────────┐                       │
│                     │ SQLite / Postgres │                    │
│                     │ (scans, items,   │                    │
│                     │  users, etc.)    │                    │
│                     └────────────────┘                       │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                Ollama Server (port 11434)                     │
│                   qwen3.5:latest                             │
│  • General Q&A                                               │
│  • Risk classification                                       │
│  • Planner (tool selection)                                  │
│  • Remediation drafts                                        │
└──────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Frontend (Next.js 14 + TailwindCSS)
- **Login/Register** page with JWT-based auth
- **Chat Dashboard** — conversational interface where users ask privacy questions or request web searches
- **Scan Detail** pages for viewing individual findings
- Dark theme with glassmorphism design

### 2. Backend (Python FastAPI)
| Endpoint Group | Purpose |
|---------------|---------|
| `/auth` | User registration and JWT login |
| `/consent` | Explicit consent management |
| `/chat` | **Primary endpoint** — routes between Ollama (Q&A) and Serper (search) |
| `/scans` | Create, run, and retrieve scan results |
| `/items` | Item details and remediation actions |
| `/planner` | Debug endpoint for planner output |
| `/mcp` | MCP tool registry and individual tool calls |

### 3. MCP Tool Implementations
| Tool | Provider | Status |
|------|----------|--------|
| `searchWeb` | Serper.dev (Google Search) | ✅ Live |
| `classifyItems` | Ollama (qwen3.5) | ✅ Live |
| `generateRemediation` | Ollama (qwen3.5) | ✅ Live |
| `scoreRisk` | Local rules engine | ✅ Live |
| `checkBreach` | HIBP (stubbed) | ⬜ Needs API key |
| `searchSocial` | GitHub/Reddit (stubbed) | ⬜ Needs API keys |
| `reverseImageSearch` | Mocked | ⬜ Needs real API |

### 4. Data Store
- **SQLite** (default, local development) or **PostgreSQL** (production)
- Tables: `user`, `consent`, `scan`, `item`, `toolcall`

### 5. LLM Layer (Ollama)
- All LLM calls route through `ollama_client.py` to the local Ollama server
- Model: `qwen3.5:latest` (274 MB, supports thinking/reasoning)
- PII is pseudonymized before sending to the LLM
- Used for: planning, classification, remediation drafting, general Q&A

---

## Data Flow

### Chat Flow (Primary)
```
User message → /chat endpoint → Intent Detection
  ├─ General question → Ollama → reply text
  └─ Search request  → Serper API → raw results → Ollama classification → reply + search_results
```

### Scan Flow (Legacy/Programmatic)
```
Create scan → Planner (Ollama) → Tool calls → Store items → Classify (Ollama) → Report
```

---

## Security & Privacy
- **Local-first LLM** — no data leaves the machine for AI inference
- **Pseudonymization** — identifiers are HMAC-hashed before LLM calls
- **Explicit consent** — scans require user opt-in
- **No face recognition** — reverse image search uses file-hash matching only
- **JWT auth** — stateless token-based authentication
