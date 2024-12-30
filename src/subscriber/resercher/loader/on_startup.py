from configs.database import database_postgres_settings
from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.repository.storage import RepoStorage
from src.services.publisher.publisher import NatsPublisher
from src.services.research.telegram.inspector import ResearchProcess


def initialize_research_processor() -> ResearchProcess:
    """Инициализирует ResearchProcess с помощью настроек из окружения"""
    repository = RepoStorage(
        database_session_manager=DatabaseSessionManager(database_url=database_postgres_settings.async_postgres_url)
    )

    publisher = NatsPublisher()

    process = ResearchProcess(
        repository=repository,
        notifier=None,
        publisher=publisher,
    )
    return process
