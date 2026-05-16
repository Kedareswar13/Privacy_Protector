# 🛡️ PrivacyProtector — Complete Project Walkthrough

> A line-by-line, file-by-file explanation of how the entire application works.

---

## 📋 Table of Contents

1. [The Big Picture](#the-big-picture)
2. [Project Structure](#project-structure)
3. [How a User Interaction Works (End-to-End)](#how-a-user-interaction-works)
4. [Configuration Files](#configuration-files)
5. [Backend Deep Dive](#backend-deep-dive)
6. [Frontend Deep Dive](#frontend-deep-dive)

---

## The Big Picture

PrivacyProtector is a **two-server** application:

```
┌─────────────────┐     HTTP (REST API)      ┌─────────────────┐
│   Next.js App   │ ◄──────────────────────►  │   FastAPI App   │
│  (port 3000)    │                           │  (port 8000)    │
│                 │                           │                 │
│  React UI in    │                           │  Python backend │
│  the browser    │                           │  on your PC     │
└─────────────────┘                           └────────┬────────┘
       ▲                                              │
       │ User sees this                               │ Talks to:
       │ in their browser                             ▼
                                          ┌───────────────────────┐
                                          │  Ollama (port 11434)  │
                                          │  Local AI model       │
                                          │  qwen3.5:latest       │
                                          └───────────────────────┘
                                                      │
                                          ┌───────────────────────┐
                                          │  Serper.dev API       │
                                          │  Google Search results│
                                          └───────────────────────┘
                                                      │
                                          ┌───────────────────────┐
                                          │  SQLite Database      │
                                          │  datasteward.db       │
                                          └───────────────────────┘
```

**The flow is:**
1. User opens `localhost:3000` in their browser → sees the Next.js frontend
2. Frontend makes `fetch()` calls to `localhost:8000` (FastAPI backend)
3. Backend processes the request, potentially calling Ollama (AI) or Serper (search)
4. Backend saves data to SQLite and returns the response
5. Frontend displays the result

---

## Project Structure

```
PrivacyProtector/
│
├── .env                         ← Secrets & config (never committed to git)
├── .env.example                 ← Template showing what .env needs
├── .gitignore                   ← Tells Git what to ignore
├── DECISIONS.md                 ← Architecture decision log
├── README.md                    ← Project overview
│
├── docs/
│   └── architecture.md          ← System architecture diagrams
│
├── backend/                     ← THE PYTHON SERVER (FastAPI)
│   ├── requirements.txt         ← Python packages to install
│   ├── datasteward.db           ← SQLite database (auto-created)
│   ├── .venv/                   ← Python virtual environment
│   └── app/                     ← The actual application code
│       ├── main.py              ← Entry point — creates the FastAPI app
│       ├── api/                 ← HTTP route handlers (what URLs do what)
│       ├── core/                ← Business logic & shared utilities
│       ├── db/                  ← Database models & connection
│       └── mcp_tools/           ← Individual tool implementations
│
└── frontend/                    ← THE JAVASCRIPT APP (Next.js)
    ├── package.json             ← Node.js packages & scripts
    ├── app/                     ← Pages (routes)
    ├── components/              ← Reusable UI pieces
    └── lib/                     ← Shared utilities
```

---

## How a User Interaction Works

### Flow 1: Login

```
Browser                          Frontend (Next.js)              Backend (FastAPI)              Database
  │                                    │                               │                          │
  │  User types email & password       │                               │                          │
  │ ──────────────────────────────►    │                               │                          │
  │                                    │  POST /auth/login             │                          │
  │                                    │  {email, password}            │                          │
  │                                    │ ─────────────────────────►    │                          │
  │                                    │                               │  SELECT user WHERE email │
  │                                    │                               │ ────────────────────────► │
  │                                    │                               │  ◄──── user row ──────── │
  │                                    │                               │                          │
  │                                    │                               │  Verify password hash    │
  │                                    │                               │  Create JWT token        │
  │                                    │  ◄─── {access_token} ────────│                          │
  │                                    │                               │                          │
  │                                    │  Store token + email in       │                          │
  │                                    │  localStorage                 │                          │
  │  ◄── Redirect to /dashboard ──────│                               │                          │
```

### Flow 2: General Question ("What is GDPR?")

```
Browser                    Frontend                  Backend /chat              Ollama (AI)
  │                           │                          │                         │
  │  User types question      │                          │                         │
  │ ────────────────────►     │                          │                         │
  │                           │  POST /chat              │                         │
  │                           │  + Bearer token          │                         │
  │                           │  + messages[]            │                         │
  │                           │ ───────────────────►     │                         │
  │                           │                          │  Extract user_id from   │
  │                           │                          │  JWT token              │
  │                           │                          │                         │
  │                           │                          │  Save user message to   │
  │                           │                          │  chatmessagerecord DB   │
  │                           │                          │                         │
  │                           │                          │  Intent detection:      │
  │                           │                          │  "What is GDPR?" →      │
  │                           │                          │  NOT a search request   │
  │                           │                          │                         │
  │                           │                          │  POST /api/chat         │
  │                           │                          │ ──────────────────►     │
  │                           │                          │                         │  qwen3.5
  │                           │                          │                         │  thinks...
  │                           │                          │  ◄── AI response ─────  │
  │                           │                          │                         │
  │                           │                          │  Strip <think> tags     │
  │                           │                          │  Save assistant msg     │
  │                           │                          │  to DB                  │
  │                           │                          │                         │
  │                           │  ◄── {reply, is_search:  │                         │
  │                           │       false}             │                         │
  │  ◄── Show AI response ── │                          │                         │
```

### Flow 3: Search ("Search for Elon Musk online")

```
Browser              Frontend               Backend /chat            Serper API        Ollama
  │                     │                       │                       │                │
  │  User asks search   │                       │                       │                │
  │ ──────────────►     │                       │                       │                │
  │                     │  POST /chat           │                       │                │
  │                     │ ─────────────────►    │                       │                │
  │                     │                       │  Intent: SEARCH ✓     │                │
  │                     │                       │                       │                │
  │                     │                       │  GET google results   │                │
  │                     │                       │ ──────────────────►   │                │
  │                     │                       │  ◄── 10 results ──── │                │
  │                     │                       │                       │                │
  │                     │                       │  Classify each result │                │
  │                     │                       │ ──────────────────────────────────►    │
  │                     │                       │  ◄── risk scores ────────────────────  │
  │                     │                       │                       │                │
  │                     │                       │  Summarize findings   │                │
  │                     │                       │ ──────────────────────────────────►    │
  │                     │                       │  ◄── summary text ───────────────────  │
  │                     │                       │                       │                │
  │                     │                       │  Save to DB (with     │                │
  │                     │                       │  search_results_json) │                │
  │                     │                       │                       │                │
  │                     │  ◄── {reply,          │                       │                │
  │                     │   search_results[],   │                       │                │
  │                     │   is_search: true}    │                       │                │
  │  ◄── Show results  │                       │                       │                │
  │      with risk      │                       │                       │                │
  │      labels         │                       │                       │                │
```

---

## Configuration Files

### [.env](file:///c:/Users/tejas/Desktop/PrivacyProtector/.env) — Environment Variables

```bash
APP_ENV=development              # App mode
FASTAPI_HOST=0.0.0.0             # Backend listens on all interfaces
FASTAPI_PORT=8000                # Backend port

# DATABASE_URL=postgresql://...  # Commented out → falls back to SQLite

JWT_SECRET=your_secret_here       # Secret key for signing JWT tokens
                                 # (used to verify "is this user really logged in?")

OLLAMA_BASE_URL=http://localhost:11434   # Where Ollama AI server runs
OLLAMA_MODEL=qwen3.5:latest             # Which AI model to use

SERPER_API_KEY=your_key_here      # API key for Google Search via Serper.dev

MOCK_CONNECTORS=false            # false = use real APIs; true = use fake test data
```

### [.gitignore](file:///c:/Users/tejas/Desktop/PrivacyProtector/.gitignore) — What Git Ignores

Prevents committing: `node_modules/`, `.next/`, `__pycache__/`, `.venv/`, `.env` (secrets!).

### [requirements.txt](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/requirements.txt) — Python Dependencies

```
fastapi          → Web framework (like Express for Python)
uvicorn          → Server that runs FastAPI
httpx            → HTTP client (for calling Ollama & Serper APIs)
pydantic         → Data validation (auto-validates request/response shapes)
sqlmodel         → ORM (maps Python classes to database tables)
python-jose      → JWT token creation & verification
python-dotenv    → Loads .env file into environment variables
requests         → HTTP client (fallback)
email-validator  → Validates email format
pytest           → Testing framework
jsonschema       → JSON schema validation for MCP tools
```

---

## Backend Deep Dive

### [main.py](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/app/main.py) — The Entry Point

**What it does:** Creates the FastAPI application, sets up CORS, registers all URL routes, and initializes the database.

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth, scans, planner, mcp, items, consent, chat
from .db.session import init_db

app = FastAPI(title="PrivacyProtector")
```
- Creates the main `app` object. Every route, middleware, and startup hook hangs off this.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    ...
)
```
- **CORS** = Cross-Origin Resource Sharing. Without this, the browser would block the frontend (port 3000) from calling the backend (port 8000) because they're on different "origins". This middleware says "yes, port 3000 is allowed to talk to me".

```python
@app.on_event("startup")
async def on_startup():
    init_db()
```
- When the server boots up, it calls `init_db()` which creates all database tables if they don't exist.

```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```
- Simple health check endpoint. If you visit `localhost:8000/health` and get `{"status":"ok"}`, the server is alive.

```python
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
# ... more routers
```
- Each `include_router` line mounts a group of endpoints. For example, `auth.router` with `prefix="/auth"` means all routes defined in `auth.py` will be under `/auth/...` (like `/auth/login`, `/auth/register`).

---

### [db/session.py](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/app/db/session.py) — Database Connection

**What it does:** Connects to the database. Falls back to SQLite if Postgres isn't available.

```python
ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")
DATABASE_URL = os.getenv("DATABASE_URL")
```
- Finds the project root, loads `.env`, reads the database URL.

```python
if not DATABASE_URL:
    _sqlite_path = Path(__file__).resolve().parents[1].parent / "datasteward.db"
    DATABASE_URL = f"sqlite:///{_sqlite_path}"
```
- If `DATABASE_URL` is not set (our case, since we commented it out), it creates a **local SQLite file** called `datasteward.db` in the backend folder. SQLite is a database that lives in a single file — no server needed.

```python
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)
```
- Creates the SQLAlchemy "engine" — the connection pool that all queries go through.

```python
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
```
- A **FastAPI dependency**. Every route that needs the database says `session: Session = Depends(get_session)` and gets a database session automatically. The session auto-closes when the request is done.

---

### [db/models.py](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/app/db/models.py) — Database Tables

**What it does:** Defines the shape of every database table using Python classes.

```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```
- This becomes a `user` table with columns: `id`, `email`, `hashed_password`, `created_at`.
- `primary_key=True` → auto-incrementing ID.
- `unique=True` → no two users can have the same email.
- `index=True` → makes lookups by email fast.

```python
class ChatMessageRecord(SQLModel, table=True):
    __tablename__ = "chatmessagerecord"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    role: str                          # "user" or "assistant"
    content: str                       # The actual message text
    search_results_json: Optional[str] # JSON string of search results (if any)
    is_search: bool = False            # Was this a search query?
    created_at: datetime = Field(default_factory=datetime.utcnow)
```
- **This is the key table for chat persistence.** Every message (from user and AI) is stored here with the `user_id`, so when you login again, your history is loaded from this table.

Other tables: `Consent`, `Scan`, `Item`, `ToolCall` — used for the scan pipeline feature.

---

### [core/auth_utils.py](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/app/core/auth_utils.py) — Authentication

**What it does:** Password hashing, JWT token creation/verification.

```python
def hash_password(password: str) -> str:
    salt = os.getenv("PASSWORD_SALT", "local_salt")
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
```
- Takes the plain password, adds a salt, and SHA256 hashes it. The database never stores your actual password — only the hash. Example: `"test1234"` → `"a7f3b8c9d2e1..."`.

```python
def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
```
- Creates a **JWT (JSON Web Token)** — a signed string like `eyJhbGciOi...`. It contains the `user_id` and expiry time. The frontend stores this and sends it with every request to prove "I am user #1".

```python
def decode_token(token: str) -> Optional[int]:
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    return int(payload.get("sub"))
```
- Reverses the process: takes a JWT string → extracts the `user_id`. If the token is expired or tampered with, this returns `None`.

---

### [api/auth.py](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/app/api/auth.py) — Login & Register Endpoints

**POST /auth/register** — Creates a new user:
1. Checks if email already exists in DB → returns 400 if duplicate
2. Hashes the password
3. Inserts a new `User` row
4. Returns `{user_id, email}`

**POST /auth/login** — Logs in:
1. Finds user by email
2. Verifies password hash matches
3. Creates a JWT token
4. Returns `{access_token, token_type: "bearer"}`

---

### [core/ollama_client.py](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/app/core/ollama_client.py) — Ollama AI Client

**What it does:** The bridge between the backend and your local Ollama AI server.

```python
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:latest")
```
- Reads config from `.env`. Defaults to localhost:11434 and qwen3.5.

```python
def _strip_think_tags(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
```
- **qwen3.5 is a "thinking" model** — it wraps its internal reasoning in `<think>...</think>` tags. This function removes those tags so the user only sees the clean answer.

```python
async def chat_completion(messages, *, model=None, temperature=0.3, timeout=300.0) -> str:
    payload = {
        "model": model or OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
    content = data.get("message", {}).get("content", "")
    return _strip_think_tags(content)
```
**How it works:**
1. Builds a JSON payload with the model name, conversation messages, and settings
2. Sends an HTTP POST to Ollama's `/api/chat` endpoint
3. Waits for the response (up to 300 seconds — qwen3.5 can be slow)
4. Extracts the assistant's reply text
5. Strips any `<think>` tags
6. Returns clean text

```python
async def is_available() -> bool:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        return resp.status_code == 200
```
- Quick health check — can we reach Ollama? Used before every AI call to fail gracefully if Ollama is down.

---

### [api/chat.py](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/app/api/chat.py) — The Main Chat Endpoint

**This is the heart of the application.** ~320 lines that handle everything.

#### Intent Detection

```python
_SEARCH_PATTERNS = [
    r"\bsearch\b",
    r"\bfind\b",
    r"\blook\s*up\b",
    r"\bscan\b",
    r"\bcheck\b.*\b(web|online|internet|data|breach|leak)\b",
    r"\bwhere\b.*\b(my|name|data|info|email|photo)\b",
    # ... more patterns
]

def _is_search_intent(text: str) -> bool:
    lower = text.lower()
    for pat in _SEARCH_PATTERNS:
        if re.search(pat, lower):
            return True
    return False
```
- These regex patterns detect if the user wants a web search.
- `"What is GDPR?"` → no match → general question path
- `"Search for my name online"` → matches `\bsearch\b` → search path

#### The POST /chat Endpoint

```python
@router.post("")
async def chat(request: ChatRequest, authorization = Header(None), session = Depends(get_session)):
```
- Accepts messages + optional JWT token + database session.

**Step 1: Authenticate**
```python
user_id = _extract_user_id(authorization)
```
- Extracts user_id from the Bearer token. If no token → `None` (messages won't be saved).

**Step 2: Save user message to DB**
```python
if user_id:
    user_record = ChatMessageRecord(user_id=user_id, role="user", content=last_user_msg)
    session.add(user_record)
    session.commit()
```
- Immediately saves the user's message. This is why chat persists across sessions.

**Step 3: Route based on intent**

If **search**: calls Serper → classifies with Ollama → generates summary → saves to DB
If **general**: sends to Ollama → saves reply to DB

#### GET /chat/history Endpoint

```python
@router.get("/history")
async def get_chat_history(authorization, session):
    user_id = _extract_user_id(authorization)
    records = session.exec(
        select(ChatMessageRecord)
        .where(ChatMessageRecord.user_id == user_id)
        .order_by(ChatMessageRecord.created_at)
    ).all()
```
- Fetches ALL messages for this user, ordered by time. This is called by the frontend when the dashboard loads.

#### DELETE /chat/history Endpoint

- Deletes all messages for the authenticated user. Called when "Clear Chat" is clicked.

---

### [mcp_tools/search_web.py](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/app/mcp_tools/search_web.py) — Google Search via Serper

```python
async def search_web(query: str, limit: int = 10):
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": limit}
    resp = await client.post("https://google.serper.dev/search", headers=headers, json=payload)
    data = resp.json()
    return [{"title": r["title"], "snippet": r["snippet"], "url": r["link"]} for r in data.get("organic", [])]
```
- Sends the search query to Serper.dev (a Google Search API wrapper)
- Returns a list of results with title, snippet, and URL
- If no API key is set, returns mock data

---

### [mcp_tools/classify_items.py](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/app/mcp_tools/classify_items.py) — Risk Classification

**What it does:** Takes search results and assigns a privacy risk score (0–1) to each one.

Two modes:
1. **Ollama mode** — sends results to the AI with a prompt asking it to judge privacy risk
2. **Fallback mode** — if Ollama is down, uses simple keyword rules:
```python
def _fallback_classification(items):
    for item in items:
        score = 0.3  # base score
        text = f"{item['title']} {item['snippet']}".lower()
        if any(w in text for w in ["breach", "leak", "exposed"]):
            score += 0.3
        if any(w in text for w in ["password", "ssn", "social security"]):
            score += 0.2
        # ...
```

---

### [core/planner_service.py](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/app/core/planner_service.py) — AI Planner

**What it does:** For the scan pipeline (not the chat), the planner decides *which tools to call* based on the user's seed data.

```python
async def plan(state: dict) -> dict:
    # Loads few-shot examples from planner_fewshots.json
    # Sends them + current state to Ollama
    # Gets back a JSON plan like:
    # {"actions": [{"tool": "searchWeb", "args": {"query": "John Doe"}}], "stop": false}
```

If Ollama is unavailable, returns a **mock plan** that just calls searchWeb with the user's query.

---

### Other MCP Tools (Stubbed)

| File | What it would do | Current status |
|------|-----------------|---------------|
| [check_breach.py](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/app/mcp_tools/check_breach.py) | Check HaveIBeenPwned for email breaches | Returns empty (needs HIBP API key) |
| [search_social.py](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/app/mcp_tools/search_social.py) | Search GitHub/Reddit for mentions | Returns empty (needs tokens) |
| [reverse_image_search.py](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/app/mcp_tools/reverse_image_search.py) | Find where an image appears online | Returns empty (needs API) |
| [score_risk.py](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/app/mcp_tools/score_risk.py) | Rule-based risk scoring | ✅ Works (no external API needed) |
| [generate_remediation.py](file:///c:/Users/tejas/Desktop/PrivacyProtector/backend/app/mcp_tools/generate_remediation.py) | Draft takedown emails | ✅ Works via Ollama |

---

## Frontend Deep Dive

### [lib/api.ts](file:///c:/Users/tejas/Desktop/PrivacyProtector/frontend/lib/api.ts) — API Client

**What it does:** All communication with the backend happens through this file.

```typescript
const API_BASE = "http://localhost:8000";
```
- Every API call goes to this base URL.

```typescript
async function apiRequest<T>(path: string, options = {}): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        ...rest,
        headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
    });
    if (!res.ok) throw new Error(`API ${res.status}: ${text}`);
    return await res.json();
}
```
- **Generic fetch wrapper.** Adds JSON content-type and optional auth token automatically.

Key functions:
- `login(email, password)` → POST `/auth/login` → returns JWT token
- `register(email, password)` → POST `/auth/register`
- `sendChat(token, messages)` → POST `/chat` → returns AI reply + optional search results
- `getChatHistory(token)` → GET `/chat/history` → returns all saved messages
- `clearChatHistory(token)` → DELETE `/chat/history`

---

### [app/page.tsx](file:///c:/Users/tejas/Desktop/PrivacyProtector/frontend/app/page.tsx) — Login / Register Page

**What it does:** The landing page with a login/register form.

```tsx
const [isLogin, setIsLogin] = useState(true);  // Toggle between Login/Register
const [email, setEmail] = useState("");
const [password, setPassword] = useState("");
```

On submit:
```tsx
if (isLogin) {
    const res = await login(email, password);
    localStorage.setItem("pp_token", res.access_token);  // Save JWT
    localStorage.setItem("pp_email", email);              // Save email for display
    window.location.href = "/dashboard";                  // Navigate to chat
} else {
    await register(email, password);        // Create account
    const res = await login(email, password); // Then auto-login
    // ... same as above
}
```

---

### [app/dashboard/page.tsx](file:///c:/Users/tejas/Desktop/PrivacyProtector/frontend/app/dashboard/page.tsx) — The Chat Dashboard

**This is the main UI the user interacts with.** Here's how it works:

#### On Page Load

```tsx
useEffect(() => {
    const t = localStorage.getItem("pp_token");
    if (!t) { router.replace("/"); return; }   // No token → go to login
    setToken(t);
    
    const email = localStorage.getItem("pp_email");
    if (email) setUserEmail(email);  // Show email in header badge
    
    // Load chat history from SERVER (not localStorage!)
    const history = await getChatHistory(t);
    setMessages(history.map(h => ({
        role: h.role,
        content: h.content,
        searchResults: h.search_results,
        isSearch: h.is_search,
        timestamp: new Date(h.created_at).getTime(),
    })));
}, []);
```
- Checks for JWT token. If missing, redirects to login.
- Loads email for the profile badge.
- **Fetches ALL chat history from the server** — this is why messages persist across sessions.

#### Sending a Message

```tsx
async function handleSend(e) {
    // 1. Add user message to local state immediately (optimistic)
    setMessages(prev => [...prev, userMsg]);
    
    // 2. Send last 10 messages to backend for context
    const response = await sendChat(token, chatHistory);
    
    // 3. Add AI response to local state
    setMessages(prev => [...prev, assistantMsg]);
}
```
- Only sends the last 10 messages for context (not entire history — performance).
- Backend saves both user and assistant messages to DB.

#### Rendering Messages

```tsx
{messages.map((msg, idx) => (
    <div className={msg.role === "user" ? "justify-end" : "justify-start"}>
        {/* User messages: blue bubble, right-aligned */}
        {/* AI messages: dark bubble, left-aligned */}
        
        {msg.searchResults && msg.searchResults.length > 0 && (
            // Render search result cards with risk labels
            {msg.searchResults.map(result => (
                <div>
                    <span className={riskColor(result.risk_label)}>
                        {riskIcon(result.risk_label)} {result.risk_label} Risk
                    </span>
                    <a href={result.url}>{result.title}</a>
                    <p>{result.snippet}</p>
                </div>
            ))}
        )}
    </div>
))}
```

#### UI Elements

- **User email badge** — shows the logged-in email with a colored avatar
- **"Ollama Online"** badge — green pulsing indicator
- **Clear Chat** button — calls `DELETE /chat/history`, then clears local state
- **Logout** button — clears localStorage, redirects to login
- **Quick suggestions** — "Search for my name online", "What is GDPR?", etc.
- **Typing indicator** — bouncing dots while waiting for Ollama response

---

### [app/layout.tsx](file:///c:/Users/tejas/Desktop/PrivacyProtector/frontend/app/layout.tsx) — Root Layout

Wraps every page with:
- Dark theme (`className="dark"`)
- Gradient background
- Header bar with "PP" logo and "PrivacyProtector" branding
- Container wrapper

### [components/ui/](file:///c:/Users/tejas/Desktop/PrivacyProtector/frontend/components/ui/) — UI Components

Small, reusable building blocks:
- **Button** — styled button with variants (default blue, outline, ghost)
- **Card** — dark glass-effect card container
- **Input** — styled input field with dark theme
- **Label** — form label with proper spacing

These are based on the [shadcn/ui](https://ui.shadcn.com/) pattern — minimal, composable UI primitives.

---

## Summary: The Complete Data Flow

```
1. User opens localhost:3000
2. Browser loads page.tsx (login page)
3. User enters email + password → clicks "Sign in"
4. Frontend POSTs to /auth/login → gets JWT token
5. Token + email saved to localStorage
6. Browser navigates to /dashboard
7. Dashboard loads → reads token from localStorage
8. Dashboard calls GET /chat/history with token
9. Backend decodes JWT → gets user_id → queries chatmessagerecord table
10. Returns all saved messages → frontend displays them
11. User types a question
12. Frontend POSTs to /chat with token + messages
13. Backend saves user message to DB
14. Backend checks intent:
    a. General → sends to Ollama → gets reply → saves to DB → returns
    b. Search → calls Serper → classifies with Ollama → summarizes → saves to DB → returns
15. Frontend displays the response (with search results and risk labels if applicable)
16. User clicks "Logout"
17. Frontend clears localStorage → redirects to login
18. Next login → Step 8 reloads the full history from DB
```

> [!IMPORTANT]
> **Key insight:** Chat history lives in the **SQLite database**, not in localStorage. This means your conversations persist across browsers, devices, and sessions — as long as you login with the same email.
