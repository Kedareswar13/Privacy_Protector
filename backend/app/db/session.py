import os
from typing import Generator

from sqlmodel import SQLModel, Session, create_engine


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://datasteward:password@postgres:5432/datasteward")

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    """Create tables in the database (dev-only helper)."""

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
