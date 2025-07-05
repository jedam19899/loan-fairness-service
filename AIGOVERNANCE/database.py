from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base

DATABASE_URL = "sqlite+aiosqlite:///./nokware.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # logs SQL for debugging
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_db():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
