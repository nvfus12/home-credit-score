from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import settings

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def init_db():
    """Initializes the database schema."""
    async with engine.begin() as conn:
        # Create all tables defined in models.py
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Dependency for retrieving database session in FastAPI routers."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
