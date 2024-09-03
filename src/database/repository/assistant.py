from sqlalchemy import insert, select

from src.database.postgres.models.assistants import Assistant
from src.database.repository.base import BaseRepository


class AssistantRepository(BaseRepository):

    async def save_new_assistant(self, values: dict):
        async with (self.db_session_manager.async_session_factory() as session):
            stmt = insert(Assistant).values(**values).returning(Assistant)
            new_assistant = await session.execute(stmt)
            await session.commit()
            return new_assistant.scalar_one()

    async def get_assistant(self, assistant_id):
        async with (self.db_session_manager.async_session_factory() as session):
            query = select(Assistant).filter(Assistant.assistant_id == assistant_id)
            execution = await session.execute(query)
            assistant = execution.scalar_one()
            #TODO Возвращать модель
            return assistant


