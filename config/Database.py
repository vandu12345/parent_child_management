from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config.Settings import get_settings

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URI, echo=True, future=True)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

Base = declarative_base()


async def get_session():
    try:
        async with SessionLocal() as session:
            yield session
    finally:
        await session.close()
