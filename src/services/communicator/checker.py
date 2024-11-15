from typing import Optional

from aiocache import Cache
from aiocache import cached

from src.database.exceptions.read import ObjectDoesNotExist
from src.database.repository.storage import RepoStorage
from src.schemas.communicator.checker import CheckerDTO
from src.schemas.service.research import ResearchDTOFull


class Checker:
    def __init__(self, repository: 'RepoStorage'):
        self._repository = repository

    async def check_user(self, user_telegram_id: int) -> CheckerDTO:
        """
        1. Пвроерить в базе даннх пользователь ?
        2. Проверить он в иследовании?
        3. Вернуть класс дто
        все это в паралельных корутинах ?

        :param user_telegram_id:
        :return:
        """
        try:
            user_in_db = await self._is_user_in_database(user_telegram_id)
            if not user_in_db:
                return CheckerDTO(user_telegram_id=user_telegram_id, user_in_db=False)

            user_research: Optional[int] = await self._get_user_research_id(user_telegram_id)
            is_has_info = await self._is_has_info(user_telegram_id=user_telegram_id)
            return CheckerDTO(
                user_telegram_id=user_telegram_id,
                user_in_db=True,
                user_research_id=user_research,
                is_has_info=is_has_info
            )
        except Exception as e:
            # TODO Логирование ошибки
            raise e


    async def _is_user_in_database(self, user_telegram_id: int) -> bool:
        return await self._repository.user_in_research_repo.short.check_user(
            telegram_id=user_telegram_id
        )


    async def _get_user_research_id(self, user_telegram_id: int) -> Optional[int]:
        try:
            research: Optional[
                ResearchDTOFull] = await self._repository.research_repo.short.get_research_by_participant_telegram_id(
                telegram_id=user_telegram_id
            )
            return research.research_id
        except ObjectDoesNotExist:
            return None

    async def _is_has_info(self, user_telegram_id: int = None, username: str = None) -> bool:
        try:
            result = await self._repository.user_in_research_repo.short.get_users_info_status(
                user_telegram_id=user_telegram_id,
                username=username)
            return result
        except Exception as e:
            raise e
