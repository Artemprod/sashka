from sqlalchemy.orm import selectinload, joinedload

from src.database.postgres.engine.session import DatabaseSessionManager
from sqlalchemy import delete, func, insert, select, update

from src.database.postgres.models.assistants import Assistant
from src.database.postgres.models.message import UserMessage, VoiceMessage
from src.database.postgres.models.research import Research
from src.database.postgres.models.user import User


class BaseRepository:
    ...

class ResearchRepository:
    """
    Когда мне нужны просты CRUD операции я использую этот класс
    """

    def __init__(self, session: DatabaseSessionManager):
        self.session = session

    async def save_new_research(self, values: dict):
        async with (self.session.async_session_factory() as session):
            stmt = insert(Research).values(**values).returning(Research)
            new_research = await session.execute(stmt)
            await session.commit()
            return new_research.scalar_one()


    async def get_research_by_id(self,research_id):
        """
        Достает иследование по его id со всеми вложенными в него данными
        в будущем подумать это в этом репозитории или для такого запросы отдельный репозиторий на уровень абстракции еще выше

        В выдаче испольует:

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
        async with (self.session.async_session_factory() as session):
            query = (select(Research).filter(Research.research_id == research_id))

            execute = await session.execute(query)
            research = execute.scalars().first()
            return research


    async def get_research_by_id(self,research_id):
        async with (self.session.async_session_factory() as session):
            query = (select(Research).filter(Research.research_id == research_id))
            execute = await session.execute(query)
            research = execute.scalars().first()
            return research

    async def update_research(self):
        ...

    async def change_research_status(self):
        ...

    async def get_all_researches_with_status(self, status):
        ...


class ResearchRepositoryFullModel:
    """
        Когда мне нужны сложные джонины со всей инофрмацие я использую этот класс
        """

    def __init__(self, session: DatabaseSessionManager):
        self.session = session

    async def get_research_by_id(self, research_id):
        """
        Достает иследование по его id со всеми вложенными в него данными
        в будущем подумать это в этом репозитории или для такого запросы отдельный репозиторий на уровень абстракции еще выше

        В выдаче испольует:

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
        async with (self.session.async_session_factory() as session):
            query = (
                select(Research)
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
                .options(joinedload(Research.status))
                .options(Research.telegram_client)
                .filter(Research.research_id == research_id))

            execute = await session.execute(query)
            research = execute.unique().scalars().first()
            return research

if __name__ == '__main__':
    async def run_q():
        rep = ResearchRepositoryFullModel()
