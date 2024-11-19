#
# from sqlalchemy import select, insert, delete
#
# from src.database.postgres import UserResearch, ArchivedUserResearch
# from src.database.postgres.engine.session import DatabaseSessionManager
# from src.database.postgres.models.research import Research
#
# from src.database.postgres.models.user import User
# from src.database.repository.base import BaseRepository
# from src.schemas.service.user import UserDTOFull
#
#
# class UserInResearchRepository(BaseRepository):
#     async def get_users_in_research(self, research_id: int):
#         """Получение списка пользователей, участвующих в исследовании."""
#         async with self.db_session_manager.async_session_factory() as session:
#             async with session.begin():
#                 stmt = select(UserResearch).where(UserResearch.research_id == research_id)
#                 result = await session.execute(stmt)
#                 users = result.scalars().all()
#                 return users
#
#     async def delete_all_users_in_research(self, research_id: int):
#         """Удаление всех пользователей, участвующих в исследовании."""
#         async with self.db_session_manager.async_session_factory() as session:
#             async with session.begin():
#                 stmt = delete(UserResearch).where(UserResearch.research_id == research_id)
#                 await session.execute(stmt)
#                 await session.commit()
#
# class UserInArchivedResearchRepository(BaseRepository):
#     async def put_users_in_database(self, users: list) -> list:
#         """Перенос пользователей в архивную таблицу."""
#         archived_users = []
#         async with self.db_session_manager.async_session_factory() as session:
#             async with session.begin():
#                 for user in users:
#                     values = {
#                         'user_id': user.user_id,
#                         'research_id': user.research_id,
#                         # Добавьте другие необходимые поля
#                     }
#                     stmt = insert(ArchivedUserResearch).values(**values).returning(ArchivedUserResearch)
#                     result = await session.execute(stmt)
#                     new_user = result.scalar_one()
#                     archived_users.append(UserDTOFull.model_validate(new_user, from_attributes=True))
#                 await session.commit()
#         return archived_users
#
# class InResearchRepo:
#     def __init__(self, db_session_manager: DatabaseSessionManager):
#         self.actual = UserInResearchRepository(db_session_manager)
#         self.archived = UserInArchivedResearchRepository(db_session_manager)
from functools import wraps
from typing import List, Dict, Any
from loguru import logger
from sqlalchemy import select, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.postgres import UserResearch, ArchivedUserResearch
from src.database.postgres.engine.session import DatabaseSessionManager
from src.schemas.service.user import UserDTOFull


class UserResearchTransferService:
    """Сервис для управления переносом пользователей между активными и архивными исследованиями."""

    def __init__(self, db_session_manager: DatabaseSessionManager):
        self.db_session_manager = db_session_manager

    async def _execute_transaction(self, session: AsyncSession, stmt: Any) -> Any:
        """Выполнение транзакции с обработкой ошибок."""
        try:
            result = await session.execute(stmt)
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при выполнении транзакции: {str(e)}")
            raise

    async def get_users_in_research(self, research_id: int) -> List[UserResearch]:
        """Получение списка пользователей в исследовании."""
        async with self.db_session_manager.async_session_factory() as session:
            stmt = select(UserResearch).where(UserResearch.research_id == research_id)
            result = await self._execute_transaction(session, stmt)
            return result.scalars().all()

    async def archive_users(self, users: List[UserResearch]) -> List[UserDTOFull]:
        """Архивирование пользователей."""
        archived_users = []
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                for user in users:
                    values = self._prepare_archive_values(user)
                    stmt = insert(ArchivedUserResearch).values(**values).returning(ArchivedUserResearch)
                    result = await self._execute_transaction(session, stmt)
                    archived_user = result.scalar_one()
                    archived_users.append(UserDTOFull.model_validate(archived_user, from_attributes=True))
            await session.commit()
        return archived_users

    async def delete_users_from_research(self, research_id: int) -> None:
        """Удаление пользователей из исследования."""
        async with self.db_session_manager.async_session_factory() as session:
            stmt = delete(UserResearch).where(UserResearch.research_id == research_id)
            await self._execute_transaction(session, stmt)

    @staticmethod
    def _prepare_archive_values(user: UserResearch) -> Dict[str, Any]:
        """Подготовка данных для архивирования."""
        return {
            'user_id': user.user_id,
            'research_id': user.research_id,
        }




class InResearchRepo:
    """Репозиторий для работы с исследованиями."""

    def __init__(self, db_session_manager: DatabaseSessionManager):
        self.transfer_service = UserResearchTransferService(db_session_manager)