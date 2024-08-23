from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.repository.client import ClientRepository


class BaseRepoStorage:

    def __init__(self, database_session_manager: DatabaseSessionManager):
        self._db_manager = database_session_manager


class RepoStorage(BaseRepoStorage):
    def __init__(self, database_session_manager: DatabaseSessionManager):
        super().__init__(database_session_manager)
        self._client_repo = ClientRepository(self._db_manager)

    @property
    def client_repo(self):
        return self._client_repo
