import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import auth, scans, planner, mcp, items, consent, chat
from .db.session import init_db


logger = logging.getLogger("privacyprotector")

app = FastAPI(title="PrivacyProtector API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler — catches ANY unhandled error so the server
#    never returns a raw 500 stack trace to the user.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
    logger.debug(traceback.format_exc())

    # Return a clean, user-friendly JSON error instead of crashing
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "error_type": type(exc).__name__,
        },
    )


@app.on_event("startup")
async def on_startup() -> None:
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as exc:
        logger.error("Failed to initialize database: %s", exc)
        logger.debug(traceback.format_exc())
        # Don't crash the server — endpoints that need the DB will fail
        # gracefully on their own.


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
app.include_router(chat.router, prefix="/chat", tags=["chat"])
