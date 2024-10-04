import asyncio
from typing import Optional, Union, List

from aiocache import cached, Cache

from src.schemas.communicator.checker import CheckerDTO
from src.schemas.service.research import ResearchDTOFull
from src.schemas.service.user import UserDTORel
from src_v0.database.postgres.engine.session import DatabaseSessionManager
from src_v0.database.repository.storage import RepoStorage


class Checker:
    def __init__(self, repository: 'RepoStorage'):
        self._repository = repository

    @cached(ttl=300, cache=Cache.MEMORY)
    async def check_user(self, user_telegram_id: int) -> CheckerDTO:
        try:
            user_in_db = await self._is_user_in_database(user_telegram_id)
            print(user_in_db)
            if not user_in_db:
                return CheckerDTO(user_telegram_id=user_telegram_id, user_in_db=False)

            user_research: Optional[int] = await self._get_user_research_id(user_telegram_id)

            return CheckerDTO(
                user_telegram_id=user_telegram_id,
                user_in_db=True,
                user_research=user_research
            )
        except Exception as e:
            # TODO Логирование ошибки
            raise e

    @cached(ttl=300, cache=Cache.MEMORY)
    async def _is_user_in_database(self, user_telegram_id: int) -> bool:
        return await self._repository.user_in_research_repo.short.check_user(
            telegram_id=user_telegram_id
        )

    @cached(ttl=300, cache=Cache.MEMORY)
    async def _get_user_research_id(self, user_telegram_id: int) -> Optional[int]:
        research: Optional[
            ResearchDTOFull] = await self._repository.research_repo.get_research_by_participant_telegram_id(
            telegram_id=user_telegram_id
        )
        return research.research_id if research else None


if __name__ == '__main__':
    async def main():
        storage = RepoStorage(database_session_manager=DatabaseSessionManager(
            database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client'))
        c = Checker(repository=storage)
        result = await c.check_user(1)
        print(result)


    asyncio.run(main())
