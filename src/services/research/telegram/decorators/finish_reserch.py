from functools import wraps

from loguru import logger


def move_users_to_archive(func):
    """Декоратор для переноса пользователей в архив и их последующего удаления."""

    @wraps(func)
    async def wrapper(self, research_id: int):
        logger.info(f"Начало переноса пользователей для исследования {research_id}")
        try:
            # Выполнение основной функции
            result = await func(self, research_id)

            # Архивирование пользователей
            logger.info(f"Архивирование пользователей")
            archived = await self.repository.in_research_repo.transfer_service.transfer_users(research_id)

            if archived == -1:
                logger.warning("список пользователй в исследовании пуст")

            return result

        except Exception as e:
            logger.error(f"Ошибка при переносе пользователей: {str(e)}")
            raise

    return wrapper
