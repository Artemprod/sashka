import datetime
from operator import and_
from typing import List, Optional

from sqlalchemy.orm import joinedload

from sqlalchemy import delete, insert, select, update

from src.schemas.service.user import UserDTOFull, UserDTORel
from src_v0.database.postgres.engine.session import DatabaseSessionManager
from src_v0.database.postgres.models.enum_types import UserStatusEnum
from src_v0.database.postgres.models.many_to_many import UserResearch
from src_v0.database.postgres.models.research import Research

from src_v0.database.postgres.models.message import UserMessage, VoiceMessage, AssistantMessage

from src_v0.database.postgres.models.status import UserStatus

from src_v0.database.postgres.models.user import User
from src_v0.database.repository.base import BaseRepository


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
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                # Сначала получить всех существующих пользователей по tg_user_id
                user_ids_to_check = [value['tg_user_id'] for value in values]
                existing_users = await session.execute(
                    select(User).where(User.tg_user_id.in_(user_ids_to_check))
                )
                existing_users = {user.tg_user_id for user in existing_users.scalars().all()}

                # Фильтруем новых пользователей, которых еще нет в базе данных
                new_users = [
                    User(**value) for value in values
                    if value['tg_user_id'] not in existing_users
                ]

                if not new_users:
                    return None

                session.add_all(new_users)
                await session.commit()
                return [UserDTOFull.model_validate(user, from_attributes=True) for user in new_users]

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[UserDTOFull]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                stmt = select(User).filter(User.tg_user_id == telegram_id)
                result = await session.execute(stmt)
                user = result.scalars().first()
                return UserDTOFull.model_validate(user, from_attributes=True) if user else None

    async def get_users_by_research_id(self, research_id: int) -> Optional[List[UserDTOFull]]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                stmt = select(User).filter(User.researches.any(Research.research_id == research_id))
                result = await session.execute(stmt)
                users = result.scalars().all()
                return [UserDTOFull.model_validate(user, from_attributes=True) for user in users]

    async def check_user(self, telegram_id: int) -> Optional[UserDTOFull]:
        async with self.db_session_manager.async_session_factory() as session:
            stmt = select(User).filter(User.tg_user_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalars().one_or_none()
            return UserDTOFull.model_validate(user, from_attributes=True) if user else None

    async def get_users_with_status(self, status: UserStatusEnum) -> Optional[List[UserDTOFull]]:
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                execution = await session.execute(
                    select(User).filter(User.status.has(UserStatus.status_name == status))
                )
                users = execution.scalars().all()
                # DONE Конгвертация в DTO
                return [UserDTOFull.model_validate(user, from_attributes=True) for user in users]

    async def get_users_by_research_with_status(self, research_id: int, status: UserStatusEnum) -> Optional[
        List[UserDTOFull]]:
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                execution = await session.execute(
                    select(User).filter(and_(User.researches.any(Research.research_id == research_id),
                                             User.status.has(UserStatus.status_name == status)))
                )
                users = execution.scalars().all()
                # DONE Конгвертация в DTO
                return [UserDTOFull.model_validate(user, from_attributes=True) for user in users]

    async def update_user_status(self, telegram_id, status: UserStatusEnum) -> UserDTOFull:
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
                return UserDTOFull.model_validate(updated.scalar_one(), from_attributes=True)

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

    async def get_user_id_by_telegram_id(self, telegram_id: int) -> int:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                stmt = select(User.user_id).filter(User.tg_user_id == telegram_id)
                result = await session.execute(stmt)
                user_id = result.first()
                return user_id[0]

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
        return (
            select(User)
            .options(joinedload(User.status))
            .options(joinedload(User.messages).joinedload(UserMessage.voice_message).joinedload(VoiceMessage.storage))
            .options(joinedload(User.assistant_messages).joinedload(AssistantMessage.assistant).joinedload(
                AssistantMessage.telegram_client))
            .options(joinedload(User.researches).joinedload(Research.assistant).joinedload(Research.status).joinedload(
                Research.telegram_client))
        )


class UserInResearchRepo:
    def __init__(self, db_session_manager: DatabaseSessionManager):
        self.short = UserRepository(db_session_manager)
        self.full = UserRepositoryFullModel(db_session_manager)
