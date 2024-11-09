from typing import List
from typing import Optional

from aiocache import Cache
from aiocache import cached
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import update

from src.database.postgres.models.assistants import Assistant
from src.database.postgres.models.research import Research
from src.database.postgres.models.user import User
from src.database.repository.base import BaseRepository
from src.schemas.service.assistant import AssistantDTOGet


class AssistantRepository(BaseRepository):
    async def save_new_assistant(self, values: dict) -> AssistantDTOGet:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                stmt = insert(Assistant).values(**values).returning(Assistant)
                new_assistant = await session.execute(stmt)
                await session.commit()
                result = new_assistant.scalar_one()
                return AssistantDTOGet.model_validate(result, from_attributes=True)

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_assistant(self, assistant_id: int) -> Optional[AssistantDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(Assistant).filter(Assistant.assistant_id == assistant_id)
            execution = await session.execute(query)
            assistant = execution.scalar_one()
            return AssistantDTOGet.model_validate(assistant, from_attributes=True)

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_assistant_by_research(self, research_id: int) -> Optional[AssistantDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(Assistant).filter(Assistant.research.has(Research.research_id == research_id))
            execution = await session.execute(query)
            assistant = execution.scalar_one()
            return AssistantDTOGet.model_validate(assistant, from_attributes=True)

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_assistant_by_user_tgelegram_id(self, telegram_id: int) -> Optional[AssistantDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            research_subquery = select(Research.assistant_id).where(
                Research.users.any(User.tg_user_id == telegram_id)).scalar_subquery()
            query = select(Assistant).filter(Assistant.research.has(Research.research_id == research_subquery))
            execution = await session.execute(query)
            assistant = execution.scalar_one_or_none()
            if assistant:
                return AssistantDTOGet.model_validate(assistant, from_attributes=True)
            return None

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_all_assistants(self) -> Optional[List[AssistantDTOGet]]:
        async with self.db_session_manager.async_session_factory() as session:
            stmt = select(Assistant)
            execution = await session.execute(stmt)
            assistants = execution.scalars().all()
            return [AssistantDTOGet.model_validate(assistant, from_attributes=True) for assistant in assistants]

    async def update_assistant(self, assistant_id: int, values: dict) -> Optional[AssistantDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                stmt = (
                    update(Assistant)
                    .where(Assistant.assistant_id == assistant_id)
                    .values(**values)
                    .returning(Assistant)
                )
                execution = await session.execute(stmt)
                assistant = execution.scalar_one_or_none()
                return AssistantDTOGet.model_validate(assistant, from_attributes=True)
