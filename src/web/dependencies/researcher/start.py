from src.database.postgres.engine.session import DatabaseSessionManager
from src.services.publisher.publisher import NatsPublisher
from src.services.research.telegram.manager import TelegramResearchManager
from starlette.requests import Request

async def get_research_manager(request: Request) -> TelegramResearchManager:
    """Получает менеджер исследований из состояния приложения."""
    return request.app.state.research_manager


async def get_publisher(request: Request) -> NatsPublisher:
    """Получает издателя NATS из состояния приложения."""
    return request.app.state.publisher

async def get_db_session(request: Request) -> DatabaseSessionManager:
    """Получает издателя db_session из состояния приложения."""
    return request.app.state.db_session