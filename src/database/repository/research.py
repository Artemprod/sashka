from datetime import datetime

import pytz
from aiocache import Cache
from aiocache import cached
from loguru import logger
from sqlalchemy import and_, update
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload

from src.database.exceptions.read import ObjectDoesNotExist
from src.database.postgres import TelegramClient
from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.postgres.models.assistants import Assistant
from src.database.postgres.models.enum_types import ResearchStatusEnum
from src.database.postgres.models.message import UserMessage
from src.database.postgres.models.message import VoiceMessage
from src.database.postgres.models.research import Research
from src.database.postgres.models.research_owner import ResearchOwner
from src.database.postgres.models.status import ResearchStatus
from src.database.postgres.models.user import User
from src.database.repository.base import BaseRepository
from src.schemas.service.research import ResearchDTOFull
from src.schemas.service.research import ResearchDTORel


class ResearchRepository(BaseRepository):
    """
    Когда мне нужны просты CRUD операции я использую этот класс
    """

    async def save_new_research(self, values: dict) -> ResearchDTOFull:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                stmt = insert(Research).values(**values).returning(Research)
                new_research = await session.execute(stmt)
                await session.commit()
                result = new_research.scalar_one()
                return ResearchDTOFull.model_validate(result, from_attributes=True)

    async def get_research_by_id(self, research_id) -> ResearchDTOFull:
        """
        Достает иследование по его id со всеми вложенными в него данными

        :param research_id:
        :return:
        """
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                query = select(Research).filter(Research.research_id == research_id)

                execute = await session.execute(query)
                research = execute.scalars().first()
                if research:
                    return ResearchDTOFull.model_validate(research, from_attributes=True)
                else:
                    raise ObjectDoesNotExist(
                        orm_object=Research.__name__, msg=f" research with id {research_id} not found"
                    )

    async def get_research_by_owner(self, owner_id) -> ResearchDTOFull:
        """ """
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                query = select(Research).filter(Research.owner.has(ResearchOwner.owner_id == owner_id))
                execute = await session.execute(query)
                research = execute.scalars().first()
                if research:
                    return ResearchDTOFull.model_validate(research, from_attributes=True)
                else:
                    raise ObjectDoesNotExist(
                        orm_object=Research.__name__, msg=f" research with owner id {owner_id} not found"
                    )

    async def get_research_by_participant(self, user_telegram_id: int, client_telegram_id: int) -> ResearchDTOFull:
        """
        Получает объект исследования по Telegram ID участника
        и преобразует его в DTO.

        Аргументы:
            user_telegram_id (int): Telegram ID участника.
            client_telegram_id (int): Telegram ID клиента.

        Возвращает:
            ResearchDTOFull: DTO объекта исследования.

        Исключения:
            ObjectDoesNotExist: Если исследование не найдено по указанному Telegram ID.
        """
        async with self.db_session_manager.async_session_factory() as session:
            try:
                query = select(Research).where(
                    and_(
                        Research.users.any(User.tg_user_id == user_telegram_id),
                        Research.telegram_client.has(TelegramClient.telegram_client_id == client_telegram_id),
                    )
                )
                result = await session.execute(query)
                research = result.scalars().first()

                if research:
                    return ResearchDTOFull.model_validate(research, from_attributes=True)

                raise ObjectDoesNotExist(
                    orm_object=Research.__name__,
                    msg=f"Research с ID участника {user_telegram_id} не найдено",
                )

            except Exception as e:
                # Опционально: можно добавить логирование или дополнительную обработку
                raise e

    async def update_research(self, research: ResearchDTOFull):
        async with self.db_session_manager.async_session_factory() as session:
            logger.info(f"Updating research: {research}")
            async with session.begin():  # использовать транзакцию
                updated_at = datetime.now(pytz.utc).replace(tzinfo=None)

                values = {
                    "research_uuid": research.research_uuid,
                    "name": research.name,
                    "title": research.title,
                    "theme": research.theme,
                    "start_date": research.start_date,
                    "end_date": research.end_date,
                    "updated_at": updated_at,
                    "descriptions": research.descriptions,
                    "additional_information": research.additional_information,
                    "assistant_id": research.assistant_id,
                    "owner_id": research.owner_id,
                    "telegram_client_id": research.telegram_client_id,
                }
                stmt = (
                    update(Research)
                    .where(Research.research_id == research.research_id)
                    .values(**values)
                    .returning(Research)
                )

                updated_research = await session.execute(stmt)

                result = updated_research.fetchall()  # Fetch all results
                logger.info(f'Result {result}')
                if not result:
                    raise ValueError(f"Research with id {research.research_id} not found.")


    async def get_all_researches_with_status(self, status): ...


class ResearchRepositoryFullModel(BaseRepository):
    """
    Когда мне нужны сложные джонины со всей инофрмацие я использую этот класс
    """

    async def get_research_by_id(self, research_id) -> ResearchDTORel:
        """
        Достает иследование по его id со всеми вложенными в него данными

        :return:
        """
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                query = self.main_query().filter(Research.research_id == research_id)
                execute = await session.execute(query)
                research = execute.unique().scalars().first()
                if research:
                    print()
                    return ResearchDTORel.model_validate(research, from_attributes=True)
                else:
                    raise ObjectDoesNotExist(
                        orm_object=Research.__name__, msg=f" research with id: {research_id} not found"
                    )

    async def get_research_by_status(self, status_name: ResearchStatusEnum):
        """
        Достает иследование по его id со всеми вложенными в него данными

        :return:
        """
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                query = self.main_query().filter(Research.status.has(ResearchStatus.status_name == status_name))

                execute = await session.execute(query)
                research = execute.unique().scalars().all()
                if research:
                    print()
                    return ResearchDTORel.model_validate(research, from_attributes=True)
                else:
                    raise ObjectDoesNotExist(
                        orm_object=Research.__name__, msg=f" research with status: {status_name} not found"
                    )

    def main_query(self):
        """
        Шаблон запроса для иследования
        в будущем подумать это в этом репозитории или для такого запросы отдельный репозиторий на уровень абстракции еще выше

        В выдаче испольует:
        ResearchOwner
        User
            status
            UserMessage

        Assistant
            AssistantMessage

        ResearchStatusName
        TelegramClient

        :param research_id:
        :return:
        """
        query = (
            select(Research)
            .options(joinedload(Research.owner))
            .options(
                selectinload(Research.users)
                .options(selectinload(User.status))
                .options(
                    joinedload(User.messages).options(
                        joinedload(UserMessage.voice_message).options(joinedload(VoiceMessage.storage))
                    )
                )
            )
            .options(joinedload(Research.assistant).options(joinedload(Assistant.messages)))
            .options(joinedload(Research.status).load_only(ResearchStatus.status_name))
            .options(joinedload(Research.telegram_client))
        )
        return query


class ResearchRepo:
    def __init__(self, database_session_manager: DatabaseSessionManager):
        self.short = ResearchRepository(database_session_manager)
        self.full = ResearchRepositoryFullModel(database_session_manager)
