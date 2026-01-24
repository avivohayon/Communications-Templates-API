import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from src.config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True to see SQL queries (useful for debugging)
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,  # Connection pool size
    max_overflow=10  # Allow up to 10 extra connections
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevents DetachedInstanceError
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


async def get_db():
    """
    FastAPI dependency that provides a database session.
    
    Transaction Management:
    - One session per request
    - Auto-commit on success
    - Auto-rollback on error
    - Auto-close always
    
    Usage in endpoints:
    ```python
    @router.get("/templates/")
    async def get_templates(db: AsyncSession = Depends(get_db)):
        return await template_logic.get_all(db)
    ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Commit if no errors
        except Exception:
            await session.rollback()  # Rollback on any error
            raise
        # Session is automatically closed (async context manager)


async def init_db():
    """
    Initialize database tables.
    
    Note: In production, use migrations instead.
    This is kept for testing purposes.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def close_db():
    """
    Close database connections.
    
    Called on application shutdown.
    """
    await engine.dispose()
    logger.info("Database connections closed")
