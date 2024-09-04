from sqlalchemy import select

from src.database.postgres.models.enum_types import UserStatusEnum, ResearchStatusEnum
from src.database.postgres.models.status import UserStatusName, ResearchStatusName
from src.database.repository.base import BaseRepository


class UserStatusRepository(BaseRepository):

    async def get_status(self, status_name: UserStatusEnum):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                user_status_exec = await session.execute(
                    select(UserStatusName).filter(UserStatusName.status_name == status_name)
                )
                user_status = user_status_exec.scalars().first()
                return user_status


class ResearchStatusRepository(BaseRepository):

    async def get_status(self, status_name: ResearchStatusEnum):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                research_status_exec = await session.execute(
                    select(ResearchStatusName).filter(ResearchStatusName.status_name == status_name)
                )
                research_status = research_status_exec.scalars().first()
                return research_status
