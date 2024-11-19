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

            # Получение пользователей через repository
            users = await self.repository.in_research_repo.transfer_service.get_users_in_research(research_id)
            if not users:
                logger.info(f"Пользователи не найдены в исследовании {research_id}")
                return result

            # Архивирование пользователей
            logger.info(f"Архивирование {len(users)} пользователей")
            await self.repository.in_research_repo.transfer_service.archive_users(users)

            # Удаление пользователей из активного исследования
            logger.info("Удаление пользователей из активного исследования")
            await self.repository.in_research_repo.transfer_service.delete_users_from_research(research_id)

            logger.info("Перенос пользователей успешно завершен")
            return result

        except Exception as e:
            logger.error(f"Ошибка при переносе пользователей: {str(e)}")
            raise

    return wrapper