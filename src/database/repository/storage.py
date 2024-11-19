from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.repository.assistant import AssistantRepository
from src.database.repository.client import ClientRepository
from src.database.repository.message_repo import MessageRepository
from src.database.repository.owner import OwnerRepo
from src.database.repository.ping import PingPromptRepository
from src.database.repository.research import ResearchRepo
from src.database.repository.status import StatusRepo
from src.database.repository.user import UserInResearchRepo
from src.database.repository.user_in_reserach import InResearchRepo


class BaseRepoStorage:

    def __init__(self, database_session_manager: DatabaseSessionManager):
        self._db_manager = database_session_manager


class RepoStorage(BaseRepoStorage):
    def __init__(self, database_session_manager: DatabaseSessionManager):
        super().__init__(database_session_manager)
        self._client_repo = ClientRepository(self._db_manager)
        self._assistant_repo = AssistantRepository(self._db_manager)
        self._owner_repo = OwnerRepo(self._db_manager)
        self._research_repo = ResearchRepo(self._db_manager)
        self._status_repo = StatusRepo(self._db_manager)
        self._user_in_research_repo = UserInResearchRepo(self._db_manager)
        self._message_repo = MessageRepository(self._db_manager)
        self._ping_prompt_repo = PingPromptRepository(self._db_manager)
        self._in_research_repo = InResearchRepo(self._db_manager)

    @property
    def client_repo(self):
        return self._client_repo

    @property
    def assistant_repo(self):
        return self._assistant_repo

    def owner_repo(self):
        return self._owner_repo

    @property
    def research_repo(self):
        return self._research_repo

    @property
    def status_repo(self):
        return self._status_repo

    @property
    def user_in_research_repo(self):
        return self._user_in_research_repo

    @property
    def message_repo(self):
        return self._message_repo

    @property
    def ping_prompt_repo(self):
        return self._ping_prompt_repo

    @property
    def in_research_repo(self):
        return self._in_research_repo
