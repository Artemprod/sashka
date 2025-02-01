from configs.ai_api_endpoints import open_ai_api_endpoint_settings
from configs.database import database_postgres_settings
from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.repository.storage import RepoStorage
from src.services.communicator.communicator import TelegramCommunicator
from src.services.communicator.prompt_generator import ExtendedPingPromptGenerator
from src.services.communicator.request import ContextRequest, TranscribeRequest
from src.services.communicator.request import SingleRequest
from src.services.parser.user.gather_info import TelegramUserInformationCollector
from src.services.publisher.publisher import NatsPublisher
from src.services.research.telegram.inspector import StopWordChecker
from src.services.scheduler.event_handlers import handle_scheduler_event, handle_job_event, handle_missed_job
from src.services.scheduler.manager import AsyncPostgresSchedularManager, AsyncPostgresSetting

def initialize_schedular()->AsyncPostgresSchedularManager:
    # инициализация планировщика для этого сервиса
    schedular: AsyncPostgresSchedularManager = AsyncPostgresSchedularManager(
        settings=AsyncPostgresSetting(
            DATABASE_URL=database_postgres_settings.sync_postgres_url,
            TABLE_NAME="apscheduler_communicator",
        )
    )
    schedular.add_event_handler(handle_scheduler_event)
    schedular.add_event_handler(handle_job_event)
    schedular.add_event_handler(handle_missed_job)
    return schedular


def initialize_communicator(scheduler:AsyncPostgresSchedularManager) -> TelegramCommunicator:
    """Инициализирует GPTRequestHandler с помощью настроек из окружения"""
    repository = RepoStorage(
        database_session_manager=DatabaseSessionManager(database_url=database_postgres_settings.async_postgres_url)
    )

    publisher = NatsPublisher()
    info_collector = TelegramUserInformationCollector(publisher=publisher)
    single_request = SingleRequest(url=open_ai_api_endpoint_settings.single_response_url)
    context_request = ContextRequest(url=open_ai_api_endpoint_settings.context_response_url)
    transcribe_request = TranscribeRequest(url=open_ai_api_endpoint_settings.transcribe_response_url)
    prompt_generator = ExtendedPingPromptGenerator(repository=repository)
    stop_word_checker = StopWordChecker(repo=repository)

    communicator = TelegramCommunicator(
        repository=repository,
        info_collector=info_collector,
        publisher=publisher,
        prompt_generator=prompt_generator,
        single_request=single_request,
        context_request=context_request,
        transcribe_request=transcribe_request,
        stop_word_checker=stop_word_checker,
        schedular=scheduler
    )
    return communicator
