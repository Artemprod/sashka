
from src.database.repository.storage import RepoStorage
from src.services.parser.user.gather_info import TelegramUserInformationCollector
from src.services.publisher.publisher import NatsPublisher
from src.services.research.telegram.manager import TelegramResearchManager


def initialize_research_manager(repository: RepoStorage,
                                publisher: NatsPublisher,
                                ) -> TelegramResearchManager:
    """ Инициализирует GPTRequestHandler с помощью настроек из окружения """
    information_collector = TelegramUserInformationCollector(publisher=publisher)
    telegram_researcher_manger = TelegramResearchManager(repository=repository,
                                                         information_collector=information_collector)
    return telegram_researcher_manger
