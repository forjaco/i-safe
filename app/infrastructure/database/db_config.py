from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

DATABASE_URL = settings.effective_async_database_url
engine = create_async_engine(DATABASE_URL, echo=settings.DATABASE_ECHO)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db():
    """Provê a sessão async da camada de infraestrutura."""
    async with async_session() as session:
        yield session
