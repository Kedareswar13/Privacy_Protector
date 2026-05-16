import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, create_engine


# Load environment variables from the project root .env when running locally.
# File layout: PrivacyProtector/backend/app/db/session.py
# parents[0] = db, [1] = app, [2] = backend, [3] = PrivacyProtector (project root)
ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback to local SQLite if no DATABASE_URL is configured or if the
# configured Postgres URL is unreachable.
if not DATABASE_URL:
    _sqlite_path = Path(__file__).resolve().parents[1].parent / "datasteward.db"
    DATABASE_URL = f"sqlite:///{_sqlite_path}"

# SQLite needs connect_args for thread safety with FastAPI
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db() -> None:
    """Create tables in the database (dev-only helper)."""

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
