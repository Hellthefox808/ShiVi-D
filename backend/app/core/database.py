from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Handle SQLite vs PostgreSQL async URL format
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite") and not db_url.startswith("sqlite+aiosqlite"):
    db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")

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

engine = create_async_engine(
    db_url,
    **engine_kwargs,
)

# Apply performance and durability PRAGMAs for SQLite connections
if db_url.startswith("sqlite"):
    from sqlalchemy import event

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB memory page cache (up from 2MB)
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O for syscall-free reads
        cursor.execute("PRAGMA temp_store=MEMORY")  # In-memory temporary tables & sorts
        cursor.close()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
