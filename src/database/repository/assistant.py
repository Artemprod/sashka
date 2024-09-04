from sqlalchemy import insert, select, update

from src.database.postgres.models.assistants import Assistant
from src.database.repository.base import BaseRepository


class AssistantRepository(BaseRepository):

    async def save_new_assistant(self, values: dict):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                stmt = insert(Assistant).values(**values).returning(Assistant)
                new_assistant = await session.execute(stmt)
                await session.commit()
                return new_assistant.scalar_one()

    async def get_assistant(self, assistant_id):
        async with (self.db_session_manager.async_session_factory() as session):
            query = select(Assistant).filter(Assistant.assistant_id == assistant_id)
            execution = await session.execute(query)
            assistant = execution.scalar_one()
            # TODO Возвращать модель
            return assistant

    async def get_all_assistants(self):
        async with self.db_session_manager.async_session_factory() as session:
            stmt = select(Assistant)
            execution = await session.execute(stmt)
            assistants = execution.scalars().all()
            return assistants

    async def update_assistant(self, assistant_id, values: dict):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                stmt = (update(Assistant)
                        .where(Assistant.assistant_id == assistant_id)
                        .values(**values)
                        .returning(Assistant)
                        )
                execution = await session.execute(stmt)
                assistant = execution.scalar_one_or_none()
                # #TODO Возвращать модель
                return assistant
