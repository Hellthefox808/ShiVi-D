"""
Briefing: Asynchronous Database Engine, Session Factory, and Storage Optimizations.
Reason: Provides database connection abstraction supporting both local SQLite (offline laptops)
and high-concurrency PostgreSQL (cloud clusters). Employs WAL journaling, memory-mapped I/O (mmap),
and large memory caches to achieve ultra-low transaction latency during disaster event surges.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Briefing: Normalizes database URL to ensure the aiosqlite async driver is used for SQLite
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite") and not db_url.startswith("sqlite+aiosqlite"):
    db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")

# Briefing: Configure driver-specific connection parameters
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {
        "timeout": 30.0,
        "check_same_thread": False,
    }

engine_kwargs = {
    "echo": False,
    "future": True,
    "connect_args": connect_args,
    "pool_pre_ping": True if not db_url.startswith("sqlite") else False,
    "pool_recycle": 1800 if not db_url.startswith("sqlite") else 3600,
}

if not db_url.startswith("sqlite"):
    # High-concurrency connection pool settings for PostgreSQL/Enterprise deployments
    engine_kwargs.update({
        "pool_size": 25,
        "max_overflow": 50,
        "pool_timeout": 30,
    })

# Explanation: Asynchronous SQLAlchemy engine
engine = create_async_engine(
    db_url,
    **engine_kwargs,
)

# Briefing: SQLite High-Performance PRAGMA Tuning.
# Reason: By default, SQLite has small caches and synchronous fsyncs that bottleneck concurrent writes.
# We tune PRAGMAs upon connection to handle high-frequency incoming outbox event batches.
if db_url.startswith("sqlite"):
    from sqlalchemy import event

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # WAL mode permits non-blocking concurrent readers while a writer flushes
        cursor.execute("PRAGMA journal_mode=WAL")
        # NORMAL sync guarantees database integrity while minimizing disk head thrashing
        cursor.execute("PRAGMA synchronous=NORMAL")
        # 30-second busy timeout to gracefully wait out lock contention
        cursor.execute("PRAGMA busy_timeout=30000")
        # 64MB memory page cache (up from default 2MB)
        cursor.execute("PRAGMA cache_size=-64000")
        # 256MB memory-mapped I/O (mmap) for zero-copy read throughput
        cursor.execute("PRAGMA mmap_size=268435456")
        # Keep temporary tables and index sorts in RAM
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

# Explanation: Session factory producing AsyncSession instances
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Explanation: Declarative Base for all SQLAlchemy ORM models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Briefing: FastAPI dependency yielding an isolated asynchronous database session per request.
    Reason: Ensures that database transactions are scoped to the HTTP request lifecycle and reliably closed.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

