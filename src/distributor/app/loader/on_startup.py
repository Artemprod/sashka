import os

from loguru import logger

from src.database.repository.storage import RepoStorage
from src.distributor.telegram_client.pyro.client.container import ClientsManager
from src.distributor.telegram_client.pyro.client.roters.message.router import answ_router
from src.distributor.telegram_client.telethoncl.handlers.loader import find_handlers_in_directories
from src.distributor.telegram_client.telethoncl.manager.container import TelethonClientsContainer


def initialize_telethon_container(repository: RepoStorage, dev_mode=False) -> TelethonClientsContainer:
    """Инициализирует TelethonClientsContainer с помощью настроек из окружения."""

    # Путь к директории с хэндлерами относительно текущего файла
    handlers_dirs = [
        os.path.join(
            os.path.dirname(__file__),
            '..',
            '..',
            'telegram_client',
            'telethoncl',
            'handlers'
        )
    ]

    # Рекурсивно ищет все модули в директориях и собирает хендлеры
    handlers = find_handlers_in_directories(handlers_dirs)
    for handler in handlers:
        logger.info(f"Found and imported handler: {handler.__name__}")
    # Создание и возвращение контейнера TelethonClientsContainer
    container = TelethonClientsContainer(
        repository=repository,
        handlers=handlers,
    )

    return container


def initialize_pyrogram_container(repository: RepoStorage, redis_connection_manager, dev_mode=False) -> ClientsManager:
    routers = [answ_router]
    container = ClientsManager(repository=repository,
                               redis_connection_manager=redis_connection_manager,
                               routers=routers,
                               dev_mode=dev_mode)
    return container
