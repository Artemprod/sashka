from typing import List
from typing import Optional

from sqlalchemy import desc, and_
from sqlalchemy import insert
from sqlalchemy import select

from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.postgres.models.message import AssistantMessage
from src.database.postgres.models.message import UserMessage
from src.database.repository.base import BaseRepository
from src.schemas.service.message import AssistantMessageDTOGet
from src.schemas.service.message import UserMessageDTOGet


class AssistantMessageRepository(BaseRepository):
    async def save_new_message(self, values: dict) -> AssistantMessageDTOGet:
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                stmt = insert(AssistantMessage).values(**values).returning(AssistantMessage)
                new_assistant_message = await session.execute(stmt)
                await session.commit()
                result = new_assistant_message.scalar_one()
                return AssistantMessageDTOGet.model_validate(result, from_attributes=True)

    async def get_all_assistent_messages_by_user_telegram_id(self, telegram_id) -> Optional[List[AssistantMessageDTOGet]]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(AssistantMessage).filter(AssistantMessage.user_telegram_id == telegram_id)
            execution = await session.execute(query)
            messages = execution.scalars().all()
            return [AssistantMessageDTOGet.model_validate(msg, from_attributes=True) for msg in messages]

    async def get_offset_assistents_messages_by_user_telegram_id(self, telegram_id, limit=1) -> Optional[List[AssistantMessageDTOGet]]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(AssistantMessage).filter(AssistantMessage.user_telegram_id == telegram_id).limit(limit)
            execution = await session.execute(query)
            messages = execution.scalars().all()
            return [AssistantMessageDTOGet.model_validate(msg, from_attributes=True) for msg in messages]

    async def get_last_assistents_message_by_user_telegram_id(self, telegram_id) -> Optional[AssistantMessageDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(AssistantMessage).filter(AssistantMessage.user_telegram_id == telegram_id).order_by(AssistantMessage.created_at.desc()).limit(1)
            result = await session.execute(query)
            message = result.scalars().first()
            if message:
                return AssistantMessageDTOGet.model_validate(message, from_attributes=True)
            return None

    async def fetch_assistant_messages_after_user(self, telegram_id) -> Optional[List[AssistantMessageDTOGet]]:
        async with self.db_session_manager.async_session_factory() as session:
            sub = (select(UserMessage.created_at)
                    .select_from(UserMessage)
                    .where(UserMessage.user_telegram_id == telegram_id)
                    .order_by(desc(UserMessage.created_at))
                    .limit(1)
                    ).scalar_subquery()
            query = (select(AssistantMessage)
                     .select_from(AssistantMessage)
                     .filter(AssistantMessage.user_telegram_id == telegram_id, AssistantMessage.created_at > sub)
                     )
            result = await session.execute(query)
            messages = result.scalars().all()
            return [AssistantMessageDTOGet.model_validate(msg, from_attributes=True) for msg in messages]
    #TODO я не передаю чат id в будущем нужно пройтись по всей цепочки и посомтреть как формируется чат ид и использовать его
    async def fetch_context_assistant_messages_after_user(
            self, telegram_id, research_id, telegram_client_id, assistant_id
    ) -> Optional[List[AssistantMessageDTOGet]]:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                # Подзапрос для времени последнего сообщения пользователя

                last_user_message_subquery = (
                    select(UserMessage.created_at)
                    .filter(
                        and_(
                            UserMessage.user_telegram_id == telegram_id,
                            UserMessage.research_id == research_id,
                            UserMessage.telegram_client_id == telegram_client_id,
                            UserMessage.assistant_id == assistant_id
                        )
                    )
                    .order_by(desc(UserMessage.created_at))
                    .limit(1)
                )
                last_user_message_time = await session.scalar(last_user_message_subquery)

                # Базовый запрос сообщений ассистента
                assistant_messages_query = (
                    select(AssistantMessage)
                    .filter(
                        and_(
                            AssistantMessage.user_telegram_id == telegram_id,
                            AssistantMessage.research_id == research_id,
                            AssistantMessage.telegram_client_id == telegram_client_id,
                            AssistantMessage.assistant_id == assistant_id
                        )
                    )
                )

                # Добавляем условие по времени, если оно существует
                if last_user_message_time is not None:
                    assistant_messages_query = assistant_messages_query.filter(
                        AssistantMessage.created_at > last_user_message_time
                    )

                # Выполнение запроса
                result = await session.execute(assistant_messages_query)
                messages = result.scalars().all()

                # Логика возврата
                if not messages and last_user_message_time is None:
                    # Если у пользователя нет сообщений, но у ассистента есть
                    no_user_messages = (
                        select(AssistantMessage)
                        .filter(
                            and_(
                                AssistantMessage.user_telegram_id == telegram_id,
                                AssistantMessage.research_id == research_id,
                                AssistantMessage.telegram_client_id == telegram_client_id,
                                AssistantMessage.assistant_id == assistant_id
                            )
                        )
                        .limit(1)
                    )
                    assistant_result = await session.execute(no_user_messages)
                    assistant_messages_exist = assistant_result.scalar_one_or_none()

                    if assistant_messages_exist is not None:
                        return [AssistantMessageDTOGet.model_validate(assistant_messages_exist, from_attributes=True)]

                return [
                    AssistantMessageDTOGet.model_validate(msg, from_attributes=True)
                    for msg in messages
                ] if messages else []

    async def get_context_messages(self, user_telegram_id, chat_id, research_id, telegram_client_id, assistant_id):
        async with self.db_session_manager.async_session_factory() as session:
            query = (
                select(AssistantMessage)
                .filter(
                    and_(
                        AssistantMessage.user_telegram_id == user_telegram_id,
                        AssistantMessage.chat_id == chat_id,
                        AssistantMessage.research_id == research_id,
                        AssistantMessage.telegram_client_id == telegram_client_id,
                        AssistantMessage.assistant_id == assistant_id,
                    )
                )
                .order_by(AssistantMessage.created_at.asc())
            )
            result = await session.execute(query)
            messages = result.scalars().all()
            return [AssistantMessageDTOGet.model_validate(msg, from_attributes=True) for msg in messages]


class UserMessageRepository(BaseRepository):
    async def save_new_message(self, values: dict) -> UserMessageDTOGet:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():
                # используем транзакцию
                stmt = insert(UserMessage).values(**values).returning(UserMessage)
                new_user_message = await session.execute(stmt)
                await session.commit()
                result = new_user_message.scalar_one()
                return UserMessageDTOGet.from_orm(result)

    async def get_user_messages_by_user_telegram_id(self, telegram_id: int) -> List[UserMessageDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(UserMessage).filter(UserMessage.user_telegram_id == telegram_id)
            execution = await session.execute(query)
            messages = execution.scalars().all()
            return [UserMessageDTOGet.model_validate(msg) for msg in messages]

    async def get_offset_user_messages_by_user_telegram_id(self, telegram_id: int, limit: int = 1) -> List[UserMessageDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(UserMessage).filter(UserMessage.user_telegram_id == telegram_id).limit(limit)
            execution = await session.execute(query)
            messages = execution.scalars().all()
            return [UserMessageDTOGet.model_validate(msg) for msg in messages]

    async def get_last_user_message_by_user_telegram_id(self, telegram_id: int) -> Optional[UserMessageDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(UserMessage).filter(UserMessage.user_telegram_id == telegram_id).order_by(UserMessage.created_at.desc()).limit(1)
            result = await session.execute(query)
            message = result.scalars().first()
            return UserMessageDTOGet.model_validate(message) if message else None

    async def get_context_messages(self, user_telegram_id, chat_id, research_id, telegram_client_id, assistant_id):
        async with self.db_session_manager.async_session_factory() as session:
            query = (
                select(UserMessage)
                .filter(
                    and_(
                        UserMessage.user_telegram_id == user_telegram_id,
                        UserMessage.chat_id == chat_id,
                        UserMessage.research_id == research_id,
                        UserMessage.telegram_client_id == telegram_client_id,
                        UserMessage.assistant_id == assistant_id,
                    )
                )
                .order_by(UserMessage.created_at.asc())
            )
            result = await session.execute(query)
            messages = result.scalars().all()
            return [UserMessageDTOGet.model_validate(msg) for msg in messages] # Возвращаем все результаты


class MessageRepository:

    def __init__(self, database_session_manager: DatabaseSessionManager):
        self.user = UserMessageRepository(database_session_manager)
        self.assistant = AssistantMessageRepository(database_session_manager)
