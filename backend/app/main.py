from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import auth, scans, planner, mcp, items, consent
from .db.session import init_db


app = FastAPI(title="PrivacyProtector API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    # Dev-only: ensure tables exist
    init_db()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Include routers (endpoints are stubs for now)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(consent.router, prefix="/consent", tags=["consent"])
app.include_router(scans.router, prefix="/scans", tags=["scans"])
app.include_router(items.router, prefix="/items", tags=["items"])
app.include_router(planner.router, prefix="/planner", tags=["planner"])
app.include_router(mcp.router, prefix="/mcp", tags=["mcp"])
