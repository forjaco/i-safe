import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.infrastructure.database.db_config import engine
from app.infrastructure.database.models import Base
async def run():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('[+] AEGIS DATABASE FORJADO.')
if __name__ == '__main__':
    asyncio.run(run())
