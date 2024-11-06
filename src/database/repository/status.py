import datetime
from typing import Optional, List

from aiocache import cached, Cache
from sqlalchemy import select, update, insert, values

from src.schemas.service.status import UserStatusDTO, ResearchStatusDTO
from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.postgres.models.enum_types import UserStatusEnum, ResearchStatusEnum
from src.database.postgres.models.status import UserStatus, ResearchStatus
from src.database.postgres.models.user import User
from src.database.repository.base import BaseRepository


class UserStatusRepository(BaseRepository):
    async def add_user_status(self, values: dict) -> UserStatusDTO:
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                stmt = insert(UserStatus).values(**values).returning(UserStatus)
                new_user = await session.execute(stmt)
                await session.commit()
                return UserStatusDTO.model_validate(new_user.scalar(), from_attributes=True)

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_status(self, status_name: UserStatusEnum) -> Optional[UserStatusDTO]:
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                user_status_exec = await session.execute(
                    select(UserStatus).filter(UserStatus.status_name == status_name)
                )
                user_status = user_status_exec.scalar()
                return UserStatusDTO.model_validate(user_status, from_attributes=True)

    async def update_status_group_of_user(self, user_group: list[int], status: UserStatusEnum) -> Optional[
        List[UserStatusDTO]]:
        """
        Обновляет статусы у всех пользователей
        1. найти id статуса в базе
        2. для кааждого пользователя поменять
        :param user_group:
        :param status:
        :return:
        """
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                # Получить все user_id для заданных telegram_id одним запросом
                user_ids_subquery = select(User.user_id).filter(User.tg_user_id.in_(user_group)).subquery()

                # Обновить статусы всех пользователей, найденных в подзапросе
                stmt = (
                    update(UserStatus)
                    .values(status_name=status, updated_at=datetime.datetime.now())
                    .where(UserStatus.user_id.in_(select(user_ids_subquery.c.user_id)))
                    .returning(UserStatus)
                )
                result = await session.execute(stmt)
                updated_statuses = result.scalars().all()

                if updated_statuses:
                    await session.commit()
                    return [UserStatusDTO.model_validate(status, from_attributes=True) for status in updated_statuses]
                else:
                    return None

    async def update_user_status(self, user_id: int, status: UserStatusEnum) -> Optional[UserStatusDTO]:
        """
        Обновляет статус одного пользователя.

        :param user_id: Идентификатор пользователя.
        :param status: Новый статус для пользователя.
        :return: DTO с обновленным статусом пользователя или None, если пользователь не найден.
        """
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                # Обновляем статус конкретного пользователя
                stmt = (
                    update(UserStatus)
                    .values(status_name=status, updated_at=datetime.datetime.now())
                    .where(UserStatus.user_id == user_id)
                    .returning(UserStatus)
                )
                result = await session.execute(stmt)
                updated_status = result.scalar()

                if updated_status:
                    await session.commit()
                    return UserStatusDTO.model_validate(updated_status, from_attributes=True)
                else:
                    return None


class ResearchStatusRepository(BaseRepository):

    async def add_research_status(self, values: dict) -> ResearchStatusDTO:
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                stmt = insert(ResearchStatus).values(**values).returning(ResearchStatus)
                new_user = await session.execute(stmt)
                await session.commit()
                return ResearchStatusDTO.model_validate(new_user.scalar_one(), from_attributes=True)

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_status(self, status_name: ResearchStatusEnum) -> ResearchStatusDTO:
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                research_status_exec = await session.execute(
                    select(ResearchStatus).filter(ResearchStatus.status_name == status_name)
                )
                research_status = research_status_exec.scalars().first()
                return ResearchStatusDTO.model_validate(research_status, from_attributes=True)

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_research_status(self, research_id) -> ResearchStatusDTO:
        async with (self.db_session_manager.async_session_factory() as session):
            research_status_exec = await session.execute(
                select(ResearchStatus).filter(ResearchStatus.research_id == research_id)
            )
            research_status = research_status_exec.scalars().one()
            return ResearchStatusDTO.model_validate(research_status, from_attributes=True)

    async def change_research_status(self, research_id, status: ResearchStatusEnum) -> Optional[ResearchStatusDTO]:
        """
        Меняет статус исследования по id на указанный

        :param research_id:
        :param status:
        :return:
        """
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                # Обновляем статус исследования по ID
                stmt = (
                    update(ResearchStatus)
                    .where(ResearchStatus.research_id == research_id)
                    .values(status_name=status, updated_at=datetime.datetime.utcnow())
                    .returning(ResearchStatus)
                )
                result = await session.execute(stmt)
                updated_status = result.scalar_one_or_none()

                # Проверяем, был ли обновлен статус
                if updated_status:
                    await session.commit()
                    return ResearchStatusDTO.model_validate(updated_status, from_attributes=True)
                else:
                    return None


class StatusRepo:

    def __init__(self, database_session_manager: DatabaseSessionManager):
        self.user_status = UserStatusRepository(database_session_manager)
        self.research_status = ResearchStatusRepository(database_session_manager)
