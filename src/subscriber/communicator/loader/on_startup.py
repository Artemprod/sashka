from src.services.communicator.communicator import TelegramCommunicator
from src.services.communicator.prompt_generator import PromptGenerator
from src.services.communicator.request import SingleRequest, ContextRequest
from src.services.parser.user.gather_info import TelegramUserInformationCollector
from src.services.publisher.messager import NatsPublisher
from src_v0.database.postgres.engine.session import DatabaseSessionManager
from src_v0.database.repository.storage import RepoStorage


def initialize_communicator() -> TelegramCommunicator:
    """ Инициализирует GPTRequestHandler с помощью настроек из окружения """
    repository = RepoStorage(database_session_manager=DatabaseSessionManager(
        database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client'))

    publisher = NatsPublisher()
    info_collector = TelegramUserInformationCollector(publisher=publisher)
    single_request = SingleRequest()
    context_request = ContextRequest()
    prompt_generator = PromptGenerator(repository=repository)
    communicator = TelegramCommunicator(repository=repository,
                                        info_collector=info_collector,
                                        publisher=publisher,
                                        prompt_generator=prompt_generator,
                                        single_request=single_request,
                                        context_request=context_request,
                                        )
    return communicator
