import datetime

from sqlalchemy import select, update, insert, values, and_

from src_v0.database.postgres.engine.session import DatabaseSessionManager
from src_v0.database.postgres.models.enum_types import UserStatusEnum, ResearchStatusEnum
from src_v0.database.postgres.models.research import Research
from src_v0.database.postgres.models.status import UserStatus, ResearchStatus
from src_v0.database.postgres.models.user import User
from src_v0.database.repository.base import BaseRepository


class UserStatusRepository(BaseRepository):
    async def add_user_status(self, values: dict):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                stmt = insert(UserStatus).values(**values).returning(UserStatus)
                new_user = await session.execute(stmt)
                await session.commit()
                return new_user.scalar_one()

    async def get_status(self, status_name: UserStatusEnum):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                user_status_exec = await session.execute(
                    select(UserStatus).filter(UserStatus.status_name == status_name)
                )
                user_status = user_status_exec.scalars().first()
                return user_status

    async def get_users_with_status(self, status: UserStatusEnum) -> list:
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                execution = await session.execute(
                    select(User).filter(User.status.has(UserStatus.status_name == status))
                )
                users = execution.scalars().all()
                # TODO Конгвертация в DTO
                return users

    async def get_users_by_research_with_status(self, research_id:int, status: UserStatusEnum) -> list:
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                execution = await session.execute(
                    select(User).filter(and_(User.researches.any(Research.research_id==research_id),User.status.has(UserStatus.status_name == status)))
                )
                users = execution.scalars().all()
                # TODO Конгвертация в DTO
                return users

    async def change_status_one_user(self, telegram_id, status: UserStatusEnum):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                sub_user = select(User.user_id).where(User.tg_user_id == telegram_id).scalar_subquery()

                stmt = (update(UserStatus)
                        .values(status_name=status, updated_at=datetime.datetime.now())
                        .where(UserStatus.user_id == sub_user)
                        .returning(UserStatus)
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

                updated_statuses = []

                for telegram_id in user_group:
                    sub_user = select(User.user_id).where(User.tg_user_id == telegram_id).scalar_subquery()

                    stmt = (update(UserStatus)
                            .values(status_name=status, updated_at=datetime.datetime.now())
                            .where(UserStatus.user_id == sub_user)
                            .returning(UserStatus)
                            )
                    result = await session.execute(stmt)
                    updated_status = result.scalar_one_or_none()
                    if updated_status:
                        updated_statuses.append(updated_status)

                await session.commit()
                return updated_statuses


class ResearchStatusRepository(BaseRepository):

    async def add_research_status(self, values: dict):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                stmt = insert(ResearchStatus).values(**values).returning(ResearchStatus)
                new_user = await session.execute(stmt)
                await session.commit()
                return new_user.scalar_one()

    async def get_status(self, status_name: ResearchStatusEnum):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                research_status_exec = await session.execute(
                    select(ResearchStatus).filter(ResearchStatus.status_name == status_name)
                )
                research_status = research_status_exec.scalars().first()
                return research_status

    async def get_research_status(self, research_id):
        async with (self.db_session_manager.async_session_factory() as session):
            research_status_exec = await session.execute(
                select(ResearchStatus).filter(ResearchStatus.research_id == research_id)
            )
            research_status = research_status_exec.scalars().one()
            return research_status

    async def change_research_status(self, research_id, status: ResearchStatusEnum):
        """
        Меняет статус исследования по id на указанный

        :param research_id:
        :param status:
        :return:
        """
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию

                stmt = (
                    update(ResearchStatus)
                    .where(ResearchStatus.research_id == research_id)
                    .values(status_name=status, updated_at=datetime.datetime.now())
                    .returning(ResearchStatus)
                )

                execution = await session.execute(stmt)
                await session.commit()
                # TODO: сделать DTO класс
                return execution.scalars().one()


class StatusRepo:

    def __init__(self, database_session_manager: DatabaseSessionManager):
        self.user_status = UserStatusRepository(database_session_manager)
        self.research_status = ResearchStatusRepository(database_session_manager)
