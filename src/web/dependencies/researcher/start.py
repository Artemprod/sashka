from apscheduler.schedulers.background import BackgroundScheduler
from starlette.requests import Request

from configs.cloud_storage import s3_selectel_settings
from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.repository.storage import RepoStorage
from src.services.analitcs.analitic import AnalyticExcel, AnalyticCSV
from src.services.analitcs.decorator.collector import AnalyticCollector
from src.services.cloud_storage.s3.clietn import S3Client
from src.services.publisher.publisher import NatsPublisher
from src.services.research.telegram.manager import TelegramResearchManager


async def get_research_manager(request: Request) -> TelegramResearchManager:
    """Извлекает менеджер Telegram исследований из состояния приложения."""
    return request.app.state.research_manager


async def get_publisher(request: Request) -> NatsPublisher:
    """Извлекает NATS издателя из состояния приложения."""
    return request.app.state.publisher


async def get_db_session(request: Request) -> DatabaseSessionManager:
    """Извлекает менеджер сессии базы данных из состояния приложения."""
    return request.app.state.db_session


async def get_s3_report_storage() -> S3Client:
    """Извлекает s3 клиента для сохранения отчетов."""
    s3_client = S3Client(
        access_key=s3_selectel_settings.access_key,
        secret_key=s3_selectel_settings.secret_key,
        endpoint_url=s3_selectel_settings.endpoint_url,
        bucket_name="sashka-reports-bucket",
    )
    return s3_client


async def get_repository(request: Request) -> RepoStorage:
    """Извлекает репозиторий из состояния приложения."""
    return request.app.state.repository


# async def get_analytic_instruments(request: Request) -> AnalyticCollector:
#     """Извлекает CSV аналитический класс из состояния приложения."""
#     return request.app.state.analytic_collector.instrument


async def get_apscheduler(request: Request) -> BackgroundScheduler:
    """Извлекает планировщик"""
    return request.app.state.apschedular
