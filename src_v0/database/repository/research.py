from aiocache import cached, Cache
from sqlalchemy.orm import selectinload, joinedload

from src.schemas.service.research import ResearchDTOFull, ResearchDTORel
from src_v0.database.exceptions.read import ObjectDoesNotExist
from src_v0.database.postgres.engine.session import DatabaseSessionManager
from sqlalchemy import insert, select

from src_v0.database.postgres.models.enum_types import ResearchStatusEnum
from src_v0.database.postgres.models.research import Research
from src_v0.database.postgres.models.assistants import Assistant
from src_v0.database.postgres.models.message import UserMessage, VoiceMessage
from src_v0.database.postgres.models.research_owner import ResearchOwner
from src_v0.database.postgres.models.status import ResearchStatus
from src_v0.database.postgres.models.user import User
from src_v0.database.repository.base import BaseRepository


class ResearchRepository(BaseRepository):
    """
    Когда мне нужны просты CRUD операции я использую этот класс
    """

    async def save_new_research(self, values: dict) -> ResearchDTOFull:
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                stmt = insert(Research).values(**values).returning(Research)
                new_research = await session.execute(stmt)
                await session.commit()
                result = new_research.scalar_one()
                return ResearchDTOFull.model_validate(result, from_attributes=True)

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_research_by_id(self, research_id) -> ResearchDTOFull:
        """
        Достает иследование по его id со всеми вложенными в него данными

        :param research_id:
        :return:
        """
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                query = (select(Research).filter(Research.research_id == research_id))

                execute = await session.execute(query)
                research = execute.scalars().first()
                if research:
                    return ResearchDTOFull.model_validate(research, from_attributes=True)
                else:
                    raise ObjectDoesNotExist(orm_object=Research.__name__,
                                             msg=f" research with id {research_id} not found")

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_research_by_owner(self, owner_id) -> ResearchDTOFull:
        """

        """
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                query = (select(Research).filter(Research.owner.has(ResearchOwner.owner_id == owner_id)))
                execute = await session.execute(query)
                research = execute.scalars().first()
                if research:
                    return ResearchDTOFull.model_validate(research, from_attributes=True)
                else:
                    raise ObjectDoesNotExist(orm_object=Research.__name__,
                                             msg=f" research with owner id {owner_id} not found")

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_research_by_participant_telegram_id(self, telegram_id: int) -> ResearchDTOFull:
        """
        Fetches a research object by a participant's Telegram ID and validates it into a DTO.

        Args:
            telegram_id (int): The Telegram ID of the participant.

        Returns:
            ResearchDTOFull: The DTO of the research object.

        Raises:
            ObjectDoesNotExist: If no research is found for the provided Telegram ID.
        """
        async with self.db_session_manager.async_session_factory() as session:  # Proper context management
            async with session.begin():
                query = (
                    select(Research)
                    .where(Research.users.any(User.tg_user_id == telegram_id))
                # Correct use of filters with relationships
                )
                result = await session.execute(query)
                research = result.scalars().first()

                if research:
                    return ResearchDTOFull.model_validate(research, from_attributes=True)
                else:
                    raise ObjectDoesNotExist(
                        orm_object=Research.__name__,
                        msg=f"Research with participant ID {telegram_id} not found"
                    )

    async def update_research(self):
        ...

    async def get_all_researches_with_status(self, status):
        ...


class ResearchRepositoryFullModel(BaseRepository):
    """
        Когда мне нужны сложные джонины со всей инофрмацие я использую этот класс
        """

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_research_by_id(self, research_id) -> ResearchDTORel:
        """
        Достает иследование по его id со всеми вложенными в него данными

        :return:
        """
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                query = self.main_query().filter(Research.research_id == research_id)
                execute = await session.execute(query)
                research = execute.unique().scalars().first()
                if research:
                    print()
                    return ResearchDTORel.model_validate(research, from_attributes=True)
                else:
                    raise ObjectDoesNotExist(orm_object=Research.__name__,
                                             msg=f" research with id: {research_id} not found")

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_research_by_status(self, status_name: ResearchStatusEnum):
        """
        Достает иследование по его id со всеми вложенными в него данными

        :return:
        """
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                query = self.main_query().filter(Research.status.has(ResearchStatus.status_name == status_name))

                execute = await session.execute(query)
                research = execute.unique().scalars().all()
                if research:
                    print()
                    return ResearchDTORel.model_validate(research, from_attributes=True)
                else:
                    raise ObjectDoesNotExist(orm_object=Research.__name__,
                                             msg=f" research with status: {status_name} not found")

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
            .options(selectinload(Research.users)
                     .options(selectinload(User.status))
                     .options(joinedload(User.messages)
                              .options(joinedload(UserMessage.voice_message)
                                       .options(joinedload(VoiceMessage.storage))
                                       )
                              )
                     )
            .options(joinedload(Research.assistant)
                     .options(joinedload(Assistant.messages))
                     )
            .options(joinedload(Research.status).load_only(ResearchStatus.status_name))
            .options(joinedload(Research.telegram_client))
        )
        return query


class ResearchRepo:

    def __init__(self, database_session_manager: DatabaseSessionManager):
        self.short = ResearchRepository(database_session_manager)
        self.full = ResearchRepositoryFullModel(database_session_manager)
