"""
core/database.py
────────────────
Async SQLAlchemy engine, session factory, and the declarative Base used by
every model in the project.

Usage in a route:
    from core.database import get_db
    async def my_view(db: AsyncSession = Depends(get_db)): ...
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import get_settings

settings = get_settings()

# ── Engine ────────────────────────────────────────────────────────────────────
# connect_args only needed for SQLite (disables the same-thread check).
_connect_args = (
    {"check_same_thread": False}
    if settings.effective_database_url.startswith("sqlite")
    else {}
)

engine = create_async_engine(
    settings.effective_database_url,
    echo=settings.debug,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ── Base ──────────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Shared declarative base — all models inherit from this."""


# ── Dependency ────────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create tables at development startup."""
    async with engine.begin() as conn:
        from app.users import models as _  # noqa: F401 — ensure all models imported
        from app.transactions import models as _  # noqa: F401
        from app.financial_planning import models as _  # noqa: F401
        from app.ai_assistant import models as _  # noqa: F401
        from app.credit_score import models as _  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)
