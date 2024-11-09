from typing import List
from typing import Optional

from sqlalchemy import desc
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
            query = select(AssistantMessage).filter(AssistantMessage.to_user_id == telegram_id)
            execution = await session.execute(query)
            messages = execution.scalars().all()
            return [AssistantMessageDTOGet.model_validate(msg, from_attributes=True) for msg in messages]

    async def get_offset_assistents_messages_by_user_telegram_id(self, telegram_id, limit=1) -> Optional[List[AssistantMessageDTOGet]]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(AssistantMessage).filter(AssistantMessage.to_user_id == telegram_id).limit(limit)
            execution = await session.execute(query)
            messages = execution.scalars().all()
            return [AssistantMessageDTOGet.model_validate(msg, from_attributes=True) for msg in messages]

    async def get_last_assistents_message_by_user_telegram_id(self, telegram_id) -> Optional[AssistantMessageDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(AssistantMessage).filter(AssistantMessage.to_user_id == telegram_id).order_by(AssistantMessage.created_at.desc()).limit(1)
            result = await session.execute(query)
            message = result.scalars().first()
            if message:
                return AssistantMessageDTOGet.model_validate(message, from_attributes=True)
            return None

    async def fetch_assistant_messages_after_user(self, telegram_id) -> Optional[List[AssistantMessageDTOGet]]:
        async with self.db_session_manager.async_session_factory() as session:
            sub = (select(UserMessage.created_at)
                    .select_from(UserMessage)
                    .where(UserMessage.from_user == telegram_id)
                    .order_by(desc(UserMessage.created_at))
                    .limit(1)
                    ).scalar_subquery()
            query = (select(AssistantMessage)
                     .select_from(AssistantMessage)
                     .filter(AssistantMessage.to_user_id == telegram_id, AssistantMessage.created_at > sub)
                     )
            result = await session.execute(query)
            messages = result.scalars().all()
            return [AssistantMessageDTOGet.model_validate(msg, from_attributes=True) for msg in messages]



    # async def get_message_by_date(self, assistant_id):
    #     async with (self.db_session_manager.async_session_factory() as session):
    #         query = select(Assistant).filter(Assistant.assistant_id == assistant_id)
    #         execution = await session.execute(query)
    #         assistant = execution.scalar_one()
    #         # TODO Возвращать модель
    #         return assistant

    # async def get_all_messages(self):
    #     async with self.db_session_manager.async_session_factory() as session:
    #         stmt = select(Assistant)
    #         execution = await session.execute(stmt)
    #         assistants = execution.scalars().all()
    #         return assistants


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
            query = select(UserMessage).filter(UserMessage.from_user == telegram_id)
            execution = await session.execute(query)
            messages = execution.scalars().all()
            return [UserMessageDTOGet.from_orm(msg) for msg in messages]

    async def get_offset_user_messages_by_user_telegram_id(self, telegram_id: int, limit: int = 1) -> List[UserMessageDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(UserMessage).filter(UserMessage.from_user == telegram_id).limit(limit)
            execution = await session.execute(query)
            messages = execution.scalars().all()
            return [UserMessageDTOGet.from_orm(msg) for msg in messages]

    async def get_last_user_message_by_user_telegram_id(self, telegram_id: int) -> Optional[UserMessageDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(UserMessage).filter(UserMessage.from_user == telegram_id).order_by(UserMessage.created_at.desc()).limit(1)
            result = await session.execute(query)
            message = result.scalars().first()
            return UserMessageDTOGet.from_orm(message) if message else None



class MessageRepository:

    def __init__(self, database_session_manager: DatabaseSessionManager):
        self.user = UserMessageRepository(database_session_manager)
        self.assistant = AssistantMessageRepository(database_session_manager)
