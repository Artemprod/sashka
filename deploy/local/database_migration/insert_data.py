import asyncio
from datetime import datetime
from sqlalchemy import Table, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from container import settings
from src.database.models.base_model import ModelBase  # Импортировать базовый класс
from src.database.models.consumption.asssistant import AIAssistant

# Импортировать модель

DATABASE_URL = settings.postgres.postgres_url

data = [

    {
        'assistant': 'AI Assistant 1',
        'name': 'Assistant One',
        'assistant_prompt': 'Hello, how can I help you?',
        'user_prompt': 'User prompt example',
        'user_prompt_for_chunks': 'Chunked prompt example',
        'created_at': datetime.utcnow()

    },

    {
        'assistant': 'AI Assistant 2',
        'name': 'Assistant Two',
        'assistant_prompt': 'What can I do for you?',
        'user_prompt': 'Another user prompt example',
        'user_prompt_for_chunks': 'Another chunked prompt example',
        'created_at': datetime.utcnow()
    }

]

async def insert_data(engine):
    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False

    )
    async with async_session() as session:
        async with session.begin():
            for entry in data:
                assistant = AIAssistant(**entry)
                session.add(assistant)
            await session.commit()


async def main():
    # Используем асинхронный драйвер asyncpg
    engine = create_async_engine(DATABASE_URL, echo=True)
    # Создаем все таблицы (если они еще не созданы)
    async with engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)
    await insert_data(engine)

if __name__ == "__main__":
    asyncio.run(main())
