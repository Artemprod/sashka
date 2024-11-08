from configs.ai_api_endpoints import open_ai_api_endpoint_settings
from src.services.communicator.communicator import TelegramCommunicator
from src.services.communicator.prompt_generator import PromptGenerator, ExtendedPingPromptGenerator
from src.services.communicator.request import SingleRequest, ContextRequest
from src.services.parser.user.gather_info import TelegramUserInformationCollector
from src.services.publisher.publisher import NatsPublisher
from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.repository.storage import RepoStorage


def initialize_communicator() -> TelegramCommunicator:
    """ Инициализирует GPTRequestHandler с помощью настроек из окружения """
    repository = RepoStorage(database_session_manager=DatabaseSessionManager(
        database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client'))

    publisher = NatsPublisher()
    info_collector = TelegramUserInformationCollector(publisher=publisher)
    single_request = SingleRequest(url=open_ai_api_endpoint_settings.single_response_url)
    context_request = ContextRequest(url=open_ai_api_endpoint_settings.context_response)
    prompt_generator = ExtendedPingPromptGenerator(repository=repository)
    communicator = TelegramCommunicator(repository=repository,
                                        info_collector=info_collector,
                                        publisher=publisher,
                                        prompt_generator=prompt_generator,
                                        single_request=single_request,
                                        context_request=context_request,
                                        )
    return communicator
