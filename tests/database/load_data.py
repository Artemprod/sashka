import asyncio

from configs.database import database_postgres_settings
from src.database.postgres import ModelBase
from src.database.postgres.engine.session import DatabaseSessionManager

session = DatabaseSessionManager(database_url=database_postgres_settings.async_postgres_url)
async def create_tables():
    """
    Создать все таблицы в базе данных.
    """
    async with session.engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)

async def drop_tables():
    """
    Удалить все таблицы в базе данных.
    """
    async with session.engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.drop_all)



if __name__ == "__main__":
    asyncio.run(create_tables())
