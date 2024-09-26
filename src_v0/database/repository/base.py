
from src_v0.database.postgres.engine.session import DatabaseSessionManager


class BaseRepository:
    def __init__(self, db_session_manager: DatabaseSessionManager):
        self.db_session_manager = db_session_manager
