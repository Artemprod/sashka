import asyncio

from sqlalchemy.orm import selectinload, joinedload

from datasourse_for_test.resercch_imirtation import UserResearch
from src.database.postgres.engine.session import DatabaseSessionManager
from sqlalchemy import delete, func, insert, select, update

from src.database.postgres.models.enum_types import ResearchStatusEnum, UserStatusEnum
from src.database.postgres.models.research import Research
from src.database.postgres.models.assistants import Assistant
from src.database.postgres.models.message import UserMessage, VoiceMessage
from src.database.postgres.models.client import TelegramClient
from src.database.postgres.models.status import ResearchStatusName, UserStatusName
from src.database.postgres.models.storage import S3VoiceStorage
from src.database.postgres.models.user import User
from src.database.repository.base import BaseRepository


class UserRepository(BaseRepository):
    """
    Когда мне нужны просты CRUD операции я использую этот класс
    """

    async def add_user(self, values: dict):
        async with (self.db_session_manager.async_session_factory() as session):
            stmt = insert(User).values(**values).returning(User)
            new_user = await session.execute(stmt)
            await session.commit()
            return new_user.scalar_one()

    async def add_many_users(self, values: list[dict]) -> list:
        async with (self.db_session_manager.async_session_factory() as session):
            users = [User(**value) for value in values]
            session.add_all(users)
            await session.commit()
            # TODO Конгвертация в DTO
            return users

    async def get_user_by_telegram_id(self, telegram_id):
        async with (self.db_session_manager.async_session_factory() as session):
            execution = await session.execute(
                select(User).filter(User.tg_user_id == telegram_id)
            )
            user = execution.scalars().first()
            # TODO Конгвертация в DTO
            return user

    async def get_users_by_status(self, status:UserStatusEnum)->list:
        async with (self.db_session_manager.async_session_factory() as session):
            execution = await session.execute(
                select(User).filter(User.status.has(UserStatusName.status_name == status))
            )
            users = execution.scalars().all()
            # TODO Конгвертация в DTO
            return users

    # async def change_user_status(self,telegram_id, status:UserStatusEnum):
    #     async with (self.db_session_manager.async_session_factory() as session):
    #         execution = await session.execute(
    #             select(User)
    #             .options(joinedload(User.status))
    #             .filter(User.tg_user_id == telegram_id)
    #         )
    #         user = execution.scalars().first()

    async def change_status_group_of_user(self, user_group:list[dict], status):
        ...

    async def get_all_users_with_status(self, status):
        ...

    async def delete_user(self):
        ...




    async def get_research_by_id(self, research_id):
        """
        Достает иследование по его id со всеми вложенными в него данными
        в будущем подумать это в этом репозитории или для такого запросы отдельный репозиторий на уровень абстракции еще выше

        В выдаче испольует:

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
        async with (self.db_session_manager.async_session_factory() as session):
            query = (select(Research).filter(Research.research_id == research_id))

            execute = await session.execute(query)
            research = execute.scalars().first()
            return research

    async def get_research_by_id(self, research_id):
        async with (self.db_session_manager.async_session_factory() as session):
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
            query = self.main_query().filter(Research.status.has(ResearchStatusName.status_name == status_name))

            execute = await session.execute(query)
            research = execute.unique().scalars().all()
            return research

    def main_query(self):
        """
        Шаблон запроса для иследования
        в будущем подумать это в этом репозитории или для такого запросы отдельный репозиторий на уровень абстракции еще выше

        В выдаче испольует:

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
