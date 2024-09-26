from sqlalchemy import insert, select, update, desc, and_

from src_v0.database.postgres.engine.session import DatabaseSessionManager
from src_v0.database.postgres.models.assistants import Assistant
from src_v0.database.postgres.models.message import UserMessage, VoiceMessage, AssistantMessage
from src_v0.database.postgres.models.research import Research
from src_v0.database.postgres.models.user import User
from src_v0.database.repository.base import BaseRepository


class AssistantMessageRepository(BaseRepository):

    async def save_new_message(self, values: dict):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                stmt = insert(AssistantMessage).values(**values).returning(AssistantMessage)
                new_assistant_message = await session.execute(stmt)
                await session.commit()
                return new_assistant_message.scalar_one()

    async def get_all_assistent_messages_by_user_telegram_id(self, telegram_id):
        async with (self.db_session_manager.async_session_factory() as session):
            query = select(AssistantMessage).filter(AssistantMessage.to_user_id == telegram_id)
            execution = await session.execute(query)
            messages = execution.scalars().all()
            # TODO Возвращать модель
            return messages

    async def get_offset_assistents_messages_by_user_telegram_id(self, telegram_id, limit=1):
        async with (self.db_session_manager.async_session_factory() as session):
            query = select(AssistantMessage).filter(AssistantMessage.to_user_id == telegram_id).limit(limit)
            execution = await session.execute(query)
            messages = execution.scalars().all()
            # TODO Возвращать модель
            return messages

    async def get_last_assistents_message_by_user_telegram_id(self, telegram_id):
        async with self.db_session_manager.async_session_factory() as session:
            query = select(AssistantMessage).filter(AssistantMessage.to_user_id == telegram_id).order_by(
                AssistantMessage.created_at.desc()).limit(1)
            result = await session.execute(query)
            message = result.scalars().first()
            # TODO: Return model
            return message

    async def fetch_assistant_messages_after_user(self, telegram_id):
        async with self.db_session_manager.async_session_factory() as session:
            sub = (select(
                UserMessage.created_at
            ).select_from(UserMessage)
                   .where(UserMessage.from_user == telegram_id)
                   .order_by(desc(UserMessage.created_at))
                   .limit(1)
                   ).scalar_subquery()
            query = (select(AssistantMessage)
                     .select_from(AssistantMessage)
                     .filter(AssistantMessage.to_user_id == telegram_id,
                             AssistantMessage.created_at > sub)
                     )
            result = await session.execute(query)
            # TODO преобраховать в DTO
            return result.scalars().all()

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

    async def save_new_message(self, values: dict):
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию

                stmt = insert(UserMessage).values(**values).returning(UserMessage)
                new_user_message = await session.execute(stmt)
                await session.commit()
                return new_user_message.scalar_one()

    async def get_user_messages_by_user_telegram_id(self, telegram_id):
        async with (self.db_session_manager.async_session_factory() as session):
            query = select(UserMessage).filter(UserMessage.from_user == telegram_id)
            execution = await session.execute(query)
            messages = execution.scalars().all()
            # TODO Возвращать модель
            return messages

    async def get_offset_user_messages_by_user_telegram_id(self, telegram_id, limit=1):
        async with (self.db_session_manager.async_session_factory() as session):
            query = select(UserMessage).filter(UserMessage.from_user == telegram_id).limit(limit)
            execution = await session.execute(query)
            messages = execution.scalars().all()
            # TODO Возвращать модель
            return messages

    async def get_last_user_message_by_user_telegram_id(self, telegram_id, limit=1):
        async with self.db_session_manager.async_session_factory() as session:
            query = select(UserMessage).filter(UserMessage.from_user == telegram_id).order_by(
                UserMessage.created_at.desc()).limit(limit)
            result = await session.execute(query)
            message = result.scalars().first()
            # TODO: Return model
            return message


class MessageRepository:

    def __init__(self, database_session_manager: DatabaseSessionManager):
        self.user = UserMessageRepository(database_session_manager)
        self.assistant = AssistantMessageRepository(database_session_manager)
