import pytz
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

from configs.cloud_storage import s3_selectel_settings
from src.database.repository.storage import RepoStorage
from src.services.cloud_storage.s3.clietn import S3Client
from src.services.parser.user.gather_info import TelegramUserInformationCollector
from src.services.publisher.publisher import NatsPublisher
from src.services.research.telegram.manager import TelegramResearchManager
from configs.redis import redis_apscheduler_config


def initialize_research_manager(
    repository: RepoStorage,
    publisher: NatsPublisher,
) -> TelegramResearchManager:
    """Инициализирует GPTRequestHandler с помощью настроек из окружения"""
    information_collector = TelegramUserInformationCollector(publisher=publisher)
    telegram_researcher_manger = TelegramResearchManager(
        repository=repository, information_collector=information_collector
    )
    return telegram_researcher_manger


def initialize_apscheduler() -> AsyncIOScheduler:
    """Инициализирует планировщик для планирования задач."""

    jobstores = {
        "default": RedisJobStore(
            jobs_key=redis_apscheduler_config.jobs_key,  # Ключ для хранения заданий
            run_times_key=redis_apscheduler_config.run_times_key,  # Ключ для времени выполнения
            host=redis_apscheduler_config.host,
            port=redis_apscheduler_config.port,
            db=redis_apscheduler_config.research_start_database,
        )
    }

    scheduler = AsyncIOScheduler(jobstores=jobstores, timezone=pytz.utc)
    scheduler.start()
    return scheduler
