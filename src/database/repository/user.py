import datetime
from operator import and_
from typing import List
from typing import Optional

import sqlalchemy.exc
from loguru import logger
from sqlalchemy import delete
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload

from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.postgres.models.enum_types import UserStatusEnum
from src.database.postgres.models.many_to_many import UserResearch
from src.database.postgres.models.message import AssistantMessage
from src.database.postgres.models.message import UserMessage
from src.database.postgres.models.research import Research
from src.database.postgres.models.status import UserStatus
from src.database.postgres.models.user import User
from src.database.repository.base import BaseRepository
from src.schemas.service.user import UserDTOFull
from src.schemas.service.user import UserDTORel
from src.services.cache.service import redis_cache_decorator


class UserRepository(BaseRepository):
    """
    Репозиторий для простых CRUD операций с пользователями.
    """

    async def add_user(self, values: dict) -> Optional[UserDTOFull]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                stmt = insert(User).values(**values).returning(User)
                result = await session.execute(stmt)
                await session.commit()
                new_user = result.scalar_one()
                return UserDTOFull.model_validate(new_user, from_attributes=True)

    async def add_many_users(self, values: List[dict]) -> Optional[List[UserDTOFull]]:
        """
        Добавляет всех пользоавтелй которых нет в базе данных
        :param values:
        :return:
        """
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                # Извлекаем все  username и tg_user_id из входных данных
                usernames_to_check = [value["username"] for value in values if "username" in value]
                tg_user_ids_to_check = [value["tg_user_id"] for value in values if "tg_user_id" in value]

                # Получаем всех существующих пользователей по username
                existing_users_by_username = await session.execute(
                    select(User).where(User.username.in_(usernames_to_check))
                )
                existing_usernames = {user.username for user in existing_users_by_username.scalars().all()}

                # Получаем всех существующих пользователей по tg_user_id
                existing_users_by_tg_user_id = await session.execute(
                    select(User).where(User.tg_user_id.in_(tg_user_ids_to_check))
                )

                existing_tg_user_ids = {user.tg_user_id for user in existing_users_by_tg_user_id.scalars().all()}

                # Фильтруем только новых пользователей, которых еще нет в базе данных
                new_users = [
                    User(**value)
                    for value in values
                    if value.get("username") not in existing_usernames
                    and value.get("tg_user_id") not in existing_tg_user_ids
                ]

                # Если новых пользователей нет, возвращаем None
                if not new_users:
                    return None

                # Добавляем пользователей и фиксируем изменения
                session.add_all(new_users)
                await session.commit()

                # Возвращаем список добавленных пользователей
                return [UserDTOFull.model_validate(user, from_attributes=True) for user in new_users]

    @redis_cache_decorator(
        key="user:telegram_id:{telegram_id}",
    )
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[UserDTOFull]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                stmt = select(User).filter(User.tg_user_id == telegram_id)
                result = await session.execute(stmt)
                user = result.scalars().first()
                return UserDTOFull.model_validate(user, from_attributes=True) if user else None

    @redis_cache_decorator(
        key="user:research_id:{research_id}",
    )
    async def get_users_by_research_id(self, research_id: int) -> Optional[List[UserDTOFull]]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                stmt = select(User).filter(User.researches.any(Research.research_id == research_id))
                result = await session.execute(stmt)
                users = result.scalars().all()
                return [UserDTOFull.model_validate(user, from_attributes=True) for user in users]

    @redis_cache_decorator(
        key="user:username:{username}",
    )
    async def get_user_by_username(self, username: str) -> Optional[UserDTOFull]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                # Создаем запрос, который фильтрует пользователей по имени
                stmt = select(User).filter(User.username == username)
                result = await session.execute(stmt)
                user = result.scalar_one()
                return UserDTOFull.model_validate(user, from_attributes=True)

    @redis_cache_decorator(
        key="user:check_user:telegram_id:{telegram_id}",
    )
    async def check_user(self, telegram_id: int) -> Optional[UserDTOFull]:
        async with self.db_session_manager.async_session_factory() as session:
            stmt = select(User).filter(User.tg_user_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalars().one_or_none()
            return UserDTOFull.model_validate(user, from_attributes=True) if user else None

    async def get_users_with_status(self, status: UserStatusEnum) -> Optional[List[UserDTOFull]]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                execution = await session.execute(
                    select(User).filter(User.status.has(UserStatus.status_name == status))
                )
                users = execution.scalars().all()
                # DONE Конгвертация в DTO
                return [UserDTOFull.model_validate(user, from_attributes=True) for user in users]

    async def get_users_by_research_with_status(
        self, research_id: int, status: UserStatusEnum
    ) -> Optional[List[UserDTOFull]]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                execution = await session.execute(
                    select(User).filter(
                        and_(
                            User.researches.any(Research.research_id == research_id),
                            User.status.has(UserStatus.status_name == status),
                        )
                    )
                )
                users = execution.scalars().all()
                # DONE Конгвертация в DTO
                return [UserDTOFull.model_validate(user, from_attributes=True) for user in users]

    async def update_user_info(self, telegram_id, values):
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                # Обновляем информацию о пользователе
                stmt = update(User).where(User.tg_user_id == telegram_id).values(**values).returning(User)
                update_result = await session.execute(stmt)
                updated_user = update_result.scalar_one_or_none()

                if updated_user is None:
                    logger.error(f"User with telegram_id {telegram_id} not found")
                    raise ValueError("User not found")

                logger.info(f"User information updated for user with telegram_id {telegram_id}")
                return UserDTOFull.model_validate(updated_user, from_attributes=True)

    async def update_user_status(self, telegram_id, status: UserStatusEnum) -> Optional[UserStatusEnum]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                try:
                    sub_user = select(User.user_id).where(User.tg_user_id == telegram_id).scalar_subquery()
                    stmt = (
                        update(UserStatus)
                        .values(status_name=status, updated_at=datetime.datetime.now())
                        .where(UserStatus.user_id == sub_user)
                        .returning(UserStatus)
                    )
                    updated = await session.execute(stmt)
                    await session.commit()
                    logger.info(f"User status updated {updated}")
                    return updated.scalars().first().status_name

                except sqlalchemy.exc.SQLAlchemyError as e:
                    logger.error(f"error in update status {updated}")
                    raise e

    @redis_cache_decorator(
        key="user:user_status:telegram_id:{telegram_id}",
    )
    async def get_user_status(self, telegram_id: int) -> UserStatusEnum:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                try:
                    sub_user = select(User.user_id).where(User.tg_user_id == telegram_id).scalar_subquery()

                    stmt = select(UserStatus).where(UserStatus.user_id == sub_user)

                    user_status = await session.execute(stmt)
                    logger.info(f"Getting user status with telegram_id {telegram_id}")
                    return user_status.scalars().first().status_name

                except sqlalchemy.exc.SQLAlchemyError as e:
                    logger.error(f"Error getting user status with telegram_id {telegram_id}: {str(e)}")
                    raise e

    async def delete_user(self, telegram_id: int) -> Optional[UserDTOFull]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                stmt = delete(User).filter(User.tg_user_id == telegram_id).returning(User)
                result = await session.execute(stmt)
                await session.commit()
                deleted_user = result.scalar_one()
                return UserDTOFull.model_validate(deleted_user, from_attributes=True)

    async def bind_research(self, user_id: int, research_id: int) -> None:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                stmt = insert(UserResearch).values(user_id=user_id, research_id=research_id)
                await session.execute(stmt)
                await session.commit()

    async def get_user_id_by_telegram_id(self, telegram_id: int) -> Optional[int]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                stmt = select(User.user_id).filter(User.tg_user_id == telegram_id)
                result = await session.execute(stmt)
                user_id = result.first()
                return user_id[0] if user_id else None

    async def get_user_id_by_username(self, username: str) -> Optional[int]:
        async with self.db_session_manager.async_session_factory() as session:  # Тип: AsyncSession
            async with session.begin():
                stmt = select(User.user_id).where(User.username == username)
                result = await session.execute(stmt)
                user_id = result.first()
                # Если пользователь найден, возвращаем его ID, иначе None
                return user_id[0] if user_id else None

    async def get_many_user_ids_by_telegram_ids(self, telegram_ids: List[int]) -> List[int]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                stmt = select(User.user_id).where(User.tg_user_id.in_(telegram_ids))
                result = await session.execute(stmt)
                return [row[0] for row in result.fetchall()]

    async def get_many_user_ids_by_usernames(self, usernames: List[str]) -> List[int]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                stmt = select(User.user_id).where(User.username.in_(usernames))
                result = await session.execute(stmt)
                return [row[0] for row in result.fetchall()]

    @redis_cache_decorator(
        key="user:users_info_status:{user_telegram_id}:{username}",
    )
    async def get_users_info_status(self, user_telegram_id: int = None, username: str = None) -> bool:
        if not user_telegram_id and not username:
            logger.error("No parameter provided")
            raise ValueError("Either `user_telegram_id` or `username` must be provided")

        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                query = select(User)
                if user_telegram_id:
                    query = query.filter(User.tg_user_id == user_telegram_id)
                elif username:
                    query = query.filter(User.username == username)

                execution = await session.execute(query)
                user = execution.scalar_one_or_none()

                if user is None:
                    logger.warning("User not found")
                    return False

                return user.is_info

    async def get_usernames_in_research(self) -> Optional[List[str]]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                # Подзапрос для получения всех user_id из UserResearch
                subquery = select(UserResearch.user_id)

                # Основной запрос для получения username из User, используя подзапрос
                stmt = select(User.username).where(User.user_id.in_(subquery))

                # Выполнение запроса и получение результатов
                result = await session.execute(stmt)

                # Получение всех значений из скаляров как список
                usernames = result.scalars().all()

                return usernames

    @redis_cache_decorator(
        key="user:first_name:telegram_id:{telegram_id}",
    )
    async def get_first_name_by_telegram_id(self, telegram_id) -> Optional[List[str]]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                stmt = select(User.name).where(User.tg_user_id == telegram_id)
                # Выполнение запроса и получение результатов
                result = await session.execute(stmt)
                # Получение всех значений из скаляров как список
                usernames = result.scalar_one()
                return usernames


class UserRepositoryFullModel(BaseRepository):
    """
    Репозиторий для сложных операций с пользователями с использованием join.
    """

    async def get_user_by_id(self, telegram_id: int) -> Optional[UserDTORel]:
        """
        Возвращает пользователя по его Telegram ID с полной информацией о нем.
        """
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                query = self.main_query().filter(User.tg_user_id == telegram_id)
                result = await session.execute(query)
                user = result.unique().scalars().first()
                return UserDTORel.model_validate(user, from_attributes=True) if user else None

    async def get_users_with_status(self, status: UserStatusEnum) -> Optional[List[UserDTORel]]:
        """
        Возвращает список пользователей с определенным статусом.
        """
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                query = self.main_query().filter(User.status.has(UserStatus.status_name == status))
                result = await session.execute(query)
                users = result.unique().scalars().all()
                return [UserDTORel.model_validate(user, from_attributes=True) for user in users] if users else None

    @staticmethod
    def main_query():
        """
        Общее описание запроса для пользователя.
        """
        return select(User).options(
            selectinload(User.status).load_only(UserStatus.status_name),
            # Assuming to use selectinload & join only if necessary.
            joinedload(User.messages).selectinload(UserMessage.voice_message),
            # Select-inload each item separately
            selectinload(User.assistant_messages).selectinload(AssistantMessage.telegram_client),
            selectinload(User.assistant_messages).selectinload(AssistantMessage.assistant),
            selectinload(User.researches).selectinload(Research.assistant),
            selectinload(User.researches).selectinload(Research.status),
            selectinload(User.researches).selectinload(Research.telegram_client),
        )


class UserInResearchRepo:
    def __init__(self, db_session_manager: DatabaseSessionManager):
        self.short = UserRepository(db_session_manager)
        self.full = UserRepositoryFullModel(db_session_manager)
