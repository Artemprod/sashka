import asyncio

from sqlalchemy.orm import joinedload


from sqlalchemy import delete, insert, select, update

from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.postgres.models.enum_types import UserStatusEnum
from src.database.postgres.models.research import Research

from src.database.postgres.models.message import UserMessage, VoiceMessage, AssistantMessage
from src.database.postgres.models.research_owner import ResearchOwner

from src.database.postgres.models.status import  UserStatus

from src.database.postgres.models.user import User
from src.database.repository.base import BaseRepository


class ResearchOwnerRepository(BaseRepository):
    """
    Когда мне нужны просты CRUD операции я использую этот класс
    """

    async def add_owner(self, values: dict):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                stmt = insert(ResearchOwner).values(**values).returning(ResearchOwner)
                new_user = await session.execute(stmt)
                await session.commit()
                return new_user.scalar_one()


    async def get_owner_by_owner_id(self, owner_id):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                execution = await session.execute(
                    select(ResearchOwner).filter(ResearchOwner.owner_id == owner_id)
                )
                user = execution.scalars().first()
                # TODO Конгвертация в DTO
                return user

    async def get_owner_by_service_id(self, service_id):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                execution = await session.execute(
                    select(ResearchOwner).filter(ResearchOwner.service_owner_id == service_id)
                )
                user = execution.scalars().one_or_none()
                # TODO Конгвертация в DTO
                return user
    async def delete_owner_by_owner_id(self, owner_id):
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                stmt = delete(ResearchOwner).filter(ResearchOwner.owner_id == owner_id).returning(ResearchOwner)
                deleted = await session.execute(stmt).scalar_one()
                session.commit()
                return deleted


class ResearchOwnerRepositoryFullModel(BaseRepository):
    """
        Когда мне нужны сложные джонины со всей инофрмацие я использую этот класс
        """

    async def get_owner_by_id(self, owner_id):
        """
        Достает иследование по его id со всеми вложенными в него данными
        :return:
        """
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                query = self.main_query().filter(ResearchOwner.owner_id == owner_id)
                execute = await session.execute(query)
                research = execute.unique().scalars().first()
                return research


    def main_query(self):
        """
        Шаблон запроса для пользователя
        в будущем подумать это в этом репозитории или для такого запросы отдельный репозиторий на уровень абстракции еще выше

        В выдаче испольует:
        Services
        UserStatusName

        UserMessage
            VoiceMessage
                S3VoiceStorage

        AssistantMessage
            Assistant
            TelegramClient

        Research
            Assistant
            ResearchStatusName
            TelegramClient

        :param research_id:
        :return:
        """
        query = (
            select(ResearchOwner)
            .options(joinedload(ResearchOwner.service))
            .options(joinedload(ResearchOwner.researches)
                     .options(joinedload(Research.assistant))
                     .options(joinedload(Research.status))
                     .options(joinedload(Research.telegram_client))
                     .options(joinedload(Research.users))
                     )
        )

        return query


class OwnerRepo:

    def __init__(self,database_session_manager: DatabaseSessionManager ):
        self.short = ResearchOwnerRepository(database_session_manager)
        self.full = ResearchOwnerRepositoryFullModel(database_session_manager)

