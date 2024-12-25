from configs.database import database_postgres_settings
from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.repository.storage import RepoStorage
from src.services.communicator.prompt_generator import Prompter

# if __name__ == '__main__':
#     pomt = Prompter(repository=RepoStorage(database_session_manager=DatabaseSessionManager(database_postgres_settings.async_postgres_url)))
#