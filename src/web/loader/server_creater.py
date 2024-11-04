from loguru import logger

from src.services.parser.user.gather_info import TelegramUserInformationCollector
from src.services.publisher.publisher import NatsPublisher
from src.services.research.telegram.manager import TelegramResearchManager
from src.web.loader.on_startup import initialize_research_manager
from src.web.routers.reserach.telegram import router as research_router
from src.web.routers.account.client import router as client_router
from src.web.routers.analitics.dialog import router as dialog_router
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI

from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.repository.storage import RepoStorage


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """ Контекстный менеджер для инициализации и закрытия ресурсов приложения """
    session = DatabaseSessionManager(
        database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client')
    repository = RepoStorage(database_session_manager=session)
    publisher = NatsPublisher()

    app.state.research_manager = initialize_research_manager(publisher=publisher,
                                                            repository=repository)
    app.state.publisher = publisher
    app.state.db_session = session
    logger.info("Initialized classes")
    yield

    # Закрытие ресурсов (если необходимо)
    logger.info("Cleanup after lifespan")


def create_server(lifespan_func=lifespan):
    server = FastAPI(lifespan=lifespan_func,
                     title="APPLICATION",
                     )
    server.include_router(research_router)
    server.include_router(client_router)
    server.include_router(dialog_router)

    return server
