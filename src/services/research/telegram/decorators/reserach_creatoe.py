from functools import wraps

from loguru import logger

from src.schemas.service.owner import ResearchOwnerDTO
from src.schemas.service.research import ResearchDTOPost
from src.services.exceptions.research import EmptyUniqueNamesForNewResearchError


def unique_users_in_research(func):
    """
    Функция-декоратор, которая удаляет пользователей, уже участвующих в исследовании.
    """

    @wraps(func)
    async def wrapper(self, research: ResearchDTOPost, owner: ResearchOwnerDTO):
        # Логгирование начала фильтрации
        logger.info("Фильтруем пользователей с использованием репозитория.")

        # Получаем список пользователей, которые уже участвуют в исследовании
        users_in_research = await self._database_repository.user_in_research_repo.short.get_usernames_in_research()

        # Если в исследовании никого нет, вызываем исходную функцию
        if not users_in_research:
            return await func(self, research, owner)

        # Определение уникальных пользователей
        unique_users_names = set(research.examinees_user_names) - set(users_in_research)

        # Исключение, если нет уникальных пользователей
        if not unique_users_names:
            logger.warning("Нет уникальных пользователей для нового исследования.")
            raise EmptyUniqueNamesForNewResearchError("Список уникальных пользователей для нового исследования пуст.")

        # Обновление исследования с уникальными пользователями
        research.examinees_user_names = list(unique_users_names)
        logger.info(f"Уникальные пользователи: {unique_users_names}")

        # TODO: добавить отправку уведомлений о пользователях, уже участвующих в исследовании

        # Вызов основной функции
        return await func(self, research, owner)

    return wrapper
