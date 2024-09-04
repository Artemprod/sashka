import asyncio

from sqlalchemy.orm import selectinload, joinedload

from datasourse_for_test.resercch_imirtation import UserResearch
from src.database.postgres.engine.session import DatabaseSessionManager
from sqlalchemy import delete, func, insert, select, update

from src.database.postgres.models.enum_types import ResearchStatusEnum
from src.database.postgres.models.research import Research
from src.database.postgres.models.assistants import Assistant
from src.database.postgres.models.message import UserMessage, VoiceMessage
from src.database.postgres.models.client import TelegramClient
from src.database.postgres.models.status import ResearchStatusName
from src.database.postgres.models.storage import S3VoiceStorage
from src.database.postgres.models.user import User
from src.database.repository.base import BaseRepository


class ResearchRepository(BaseRepository):
    """
    Когда мне нужны просты CRUD операции я использую этот класс
    """

    async def save_new_research(self, values: dict):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                stmt = insert(Research).values(**values).returning(Research)
                new_research = await session.execute(stmt)
                await session.commit()
                return new_research.scalar_one()

    async def get_research_by_id(self, research_id):
        """
        Достает иследование по его id со всеми вложенными в него данными

        :param research_id:
        :return:
        """
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                query = (select(Research).filter(Research.research_id == research_id))

                execute = await session.execute(query)
                research = execute.scalars().first()
                return research
    async def get_research_by_owner(self, owner):
        """

        """
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                query = (select(Research).filter(Research.research_id == research_id))

                execute = await session.execute(query)
                research = execute.scalars().first()
                return research

    async def update_research(self):
        ...

    async def change_research_status(self):
        ...

    async def get_all_researches_with_status(self, status):
        ...


class ResearchRepositoryFullModel(BaseRepository):
    """
        Когда мне нужны сложные джонины со всей инофрмацие я использую этот класс
        """

    async def get_research_by_id(self, research_id):
        """
        Достает иследование по его id со всеми вложенными в него данными

        :return:
        """
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                query = self.main_query().filter(Research.research_id == research_id)
                execute = await session.execute(query)
                research = execute.unique().scalars().first()
                return research

    async def get_research_by_status(self, status_name: ResearchStatusEnum):
        """
        Достает иследование по его id со всеми вложенными в него данными

        :return:
        """
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                query = self.main_query().filter(Research.status.has(ResearchStatusName.status_name == status_name))

                execute = await session.execute(query)
                research = execute.unique().scalars().all()
                return research

    def main_query(self):
        """
        Шаблон запроса для иследования
        в будущем подумать это в этом репозитории или для такого запросы отдельный репозиторий на уровень абстракции еще выше

        В выдаче испольует:
        ResearchOwner
        User
            status
            UserMessage

        Assistant
            AssistantMessage

        ResearchStatusName
        TelegramClient

        :param research_id:
        :return:
        """
        query = (
            select(Research)
            .options(joinedload(Research.owner))
            .options(selectinload(Research.users)
                     .options(selectinload(User.status))
                     .options(joinedload(User.messages)
                              .options(joinedload(UserMessage.voice_message)
                                       .options(joinedload(VoiceMessage.storage))
                                       )
                              )
                     )
            .options(joinedload(Research.assistant)
                     .options(joinedload(Assistant.messages))
                     )
            .options(joinedload(Research.status).load_only(ResearchStatusName.status_name))
            .options(joinedload(Research.telegram_client))
        )
        return query
