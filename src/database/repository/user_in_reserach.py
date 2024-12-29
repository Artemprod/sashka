#
# from sqlalchemy import select, insert, delete
#
# from src.database.postgres import UserResearch, ArchivedUserResearch
# from src.database.postgres.engine.session import DatabaseSessionManager
# from src.database.postgres.mock_models.research import Research
#
# from src.database.postgres.mock_models.user import User
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
from typing import List, Dict, Any, Optional
from loguru import logger
from pyrogram.errors.exceptions.all import count
from sqlalchemy import select, insert, delete, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.postgres import UserResearch, ArchivedUserResearch
from src.database.postgres.engine.session import DatabaseSessionManager
from src.schemas.service.user import UserDTOFull


class UserResearchTransferService:
    """Сервис для управления переносом пользователей между активными и архивными исследованиями."""

    def __init__(self, db_session_manager):
        self.db_session_manager = db_session_manager

    async def transfer_users(self, research_id: int) -> Optional[int]:
        """
        Переносит пользователей из активного исследования в архив одной атомарной транзакцией.

        Args:
            research_id: ID исследования, пользователей которого нужно перенести

        Raises:
            SQLAlchemyError: при ошибках работы с БД
        """
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                try:
                    logger.info("Забираю пользователей и начинаю перенос")

                    # Проверяем, есть ли пользователи в исследовании
                    count_stmt = (
                        select(func.count()).select_from(UserResearch).where(UserResearch.research_id == research_id)
                    )
                    result = await session.execute(count_stmt)
                    user_count = result.scalar_one_or_none()

                    if user_count is None or user_count == 0:
                        logger.info(f"No users found for research {research_id}")
                        return -1

                    # Создаем INSERT ... SELECT запрос для переноса данных одной операцией
                    insert_stmt = insert(ArchivedUserResearch).from_select(
                        [
                            UserResearch.user_id,
                            UserResearch.research_id,
                            UserResearch.created_at,
                        ],  # Колонки для вставки
                        select(UserResearch.user_id, UserResearch.research_id, UserResearch.created_at).where(
                            UserResearch.research_id == research_id
                        ),
                    )

                    # Выполняем INSERT и DELETE в рамках одной транзакции
                    await session.execute(insert_stmt)
                    logger.info("Перенос пользователей успешно завершен")

                    delete_stmt = delete(UserResearch).where(UserResearch.research_id == research_id)
                    logger.info("Удаление пользователей из активного исследования")
                    result = await session.execute(delete_stmt)

                    # Логируем количество перенесенных записей
                    deleted_count = result.rowcount
                    logger.info(
                        f"Successfully transferred {deleted_count} users from research {research_id} to archive"
                    )

                except SQLAlchemyError as e:
                    logger.error(f"Failed to transfer users for research {research_id}: {str(e)}", exc_info=True)
                    raise


class InResearchRepo:
    """Репозиторий для работы с исследованиями."""

    def __init__(self, db_session_manager: DatabaseSessionManager):
        self.transfer_service = UserResearchTransferService(db_session_manager)
