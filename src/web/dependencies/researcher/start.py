from src.database.postgres.engine.session import DatabaseSessionManager
from src.services.analitcs.analitic import AnalyticCSV, AnalyticExcel
from src.services.analitcs.decorator.collector import AnalyticCollector
from src.services.publisher.publisher import NatsPublisher
from src.services.research.telegram.manager import TelegramResearchManager
from starlette.requests import Request


async def get_research_manager(request: Request) -> TelegramResearchManager:
    """Извлекает менеджер Telegram исследований из состояния приложения."""
    return request.app.state.research_manager


async def get_publisher(request: Request) -> NatsPublisher:
    """Извлекает NATS издателя из состояния приложения."""
    return request.app.state.publisher


async def get_db_session(request: Request) -> DatabaseSessionManager:
    """Извлекает менеджер сессии базы данных из состояния приложения."""
    return request.app.state.db_session


async def get_analytic_instruments(request: Request) -> AnalyticCollector:
    """Извлекает CSV аналитический класс из состояния приложения."""
    return request.app.state.analytic_collector.instruments

