
from src.services.publisher.publisher import NatsPublisher
from src.services.research.telegram.inspector import ResearchProcess
from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.repository.storage import RepoStorage


def initialize_research_processor() -> ResearchProcess:
    """ Инициализирует ResearchProcess с помощью настроек из окружения """
    repository = RepoStorage(database_session_manager=DatabaseSessionManager(
        database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client'))

    publisher = NatsPublisher()

    process = ResearchProcess(repository=repository,
                              notifier=None,
                              publisher=publisher,
                              )
    return process
