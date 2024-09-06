import asyncio

from sqlalchemy.orm import joinedload


from sqlalchemy import delete, insert, select, update

from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.postgres.models.enum_types import UserStatusEnum
from src.database.postgres.models.many_to_many import UserResearch
from src.database.postgres.models.research import Research

from src.database.postgres.models.message import UserMessage, VoiceMessage, AssistantMessage

from src.database.postgres.models.status import  UserStatusName

from src.database.postgres.models.user import User
from src.database.repository.base import BaseRepository


class UserRepository(BaseRepository):
    """
    Когда мне нужны просты CRUD операции я использую этот класс
    """

    async def add_user(self, values: dict):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                stmt = insert(User).values(**values).returning(User)
                new_user = await session.execute(stmt)
                await session.commit()
                return new_user.scalar_one()

    async def add_many_users(self, values: list[dict]) -> list:
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                users = [User(**value) for value in values]
                session.add_all(users)
                await session.commit()
                # TODO Конгвертация в DTO
                return users

    async def get_user_by_telegram_id(self, telegram_id):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                execution = await session.execute(
                    select(User).filter(User.tg_user_id == telegram_id)
                )
                user = execution.scalars().first()
                # TODO Конгвертация в DTO
                return user

    async def get_users_by_research_id(self, research_id):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                execution = await session.execute(
                    select(User).filter(User.researches.any(Research.research_id==research_id))
                )
                users = execution.scalars().all()
                # TODO Конгвертация в DTO
                return users

    async def get_users_with_status(self, status: UserStatusEnum) -> list:
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                execution = await session.execute(
                    select(User).filter(User.status.has(UserStatusName.status_name == status))
                )
                users = execution.scalars().all()
                # TODO Конгвертация в DTO
                return users

    async def change_status_one_user(self, telegram_id, status: UserStatusEnum):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                sub = (select(UserStatusName.status_id)
                       .where(UserStatusName.status_name == status)
                       .scalar_subquery())

                stmt = (update(User)
                        .values(status_id=sub)
                        .where(User.tg_user_id == telegram_id)
                        .returning(User)
                        )

                updated = await session.execute(stmt)
                await session.commit()
                return updated.scalar_one()

    async def change_status_group_of_user(self, user_group: list[int], status: UserStatusEnum):
        """
        Обновляет статусы у всех пользователей
        1. найти id статуса в базе
        2. для кааждого пользователя поменять
        :param user_group:
        :param status:
        :return:
        """
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                # Получаем идентификатор статуса
                sub = (
                    select(UserStatusName.status_id)
                    .where(UserStatusName.status_name == status)
                    .scalar_subquery()
                )

                updated_users = []

                for telegram_id in user_group:
                    stmt = (
                        update(User)
                        .values(status_id=sub)
                        .where(User.tg_user_id == telegram_id)
                        .returning(User)
                    )
                    result = await session.execute(stmt)
                    updated_user = result.scalar_one_or_none()
                    if updated_user:
                        updated_users.append(updated_user)

                await session.commit()
                return updated_users

    async def delete_user(self, telegram_id):
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                stmt = delete(User).filter(User.tg_user_id == telegram_id).returning(User)
                deleted = await session.execute(stmt).scalar_one()
                session.commit()
                return deleted

    async def bind_research(self, user_id, research_id):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                stmt = insert(UserResearch).values(user_id=user_id,research_id=research_id)
                await session.execute(stmt)

class UserRepositoryFullModel(BaseRepository):
    """
        Когда мне нужны сложные джонины со всей инофрмацие я использую этот класс
        """

    async def get_user_by_id(self, telegram_id):
        """
        Достает иследование по его id со всеми вложенными в него данными

        :return:
        """
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                query = self.main_query().filter(User.tg_user_id == telegram_id)
                execute = await session.execute(query)
                research = execute.unique().scalars().first()
                return research

    async def get_users_with_status(self, status: UserStatusEnum):
        """
        Достает иследование по его id со всеми вложенными в него данными

        :return:
        """
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():
                query = self.main_query().filter(User.status.has(UserStatusName.status_name == status))
                execute = await session.execute(query)
                research = execute.unique().scalars().all()
                return research

    def main_query(self):
        """
        Шаблон запроса для пользователя
        в будущем подумать это в этом репозитории или для такого запросы отдельный репозиторий на уровень абстракции еще выше

        В выдаче испольует:

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
            select(User)
            .options(joinedload(User.status))
            .options(joinedload(User.messages)
                     .options(joinedload(UserMessage.voice_message)
                              .options(joinedload(VoiceMessage.storage))
                              )
                     )
            .options(joinedload(User.assistant_messages)
                     .options(joinedload(AssistantMessage.assistant))
                     .options(joinedload(AssistantMessage.telegram_client))
                     )
            .options(joinedload(User.researches)
                     .options(joinedload(Research.assistant))
                     .options(joinedload(Research.status))
                     .options(joinedload(Research.telegram_client))
                     )
        )

        return query


class UserInResearchRepo:

    def __init__(self, database_session_manager: DatabaseSessionManager):
        self.short = UserRepository(database_session_manager)
        self.full = UserRepositoryFullModel(database_session_manager)

