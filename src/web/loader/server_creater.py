import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from loguru import logger
from starlette.staticfiles import StaticFiles

from configs.database import database_postgres_settings
from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.repository.storage import RepoStorage
from src.services.analitcs.decorator.collector import AnalyticCollector
from src.services.publisher.publisher import NatsPublisher
from src.web.loader.on_startup import initialize_research_manager, initialize_apscheduler
from src.web.routers.account.client import router as client_router
from src.web.routers.analitics.dialog import router as dialog_router
from src.web.routers.configuration.configuration import router as configuration_router
from src.web.routers.reserach.telegram import router as research_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Контекстный менеджер для инициализации и закрытия ресурсов приложения"""
    session = DatabaseSessionManager(database_url=database_postgres_settings.async_postgres_url)
    repository = RepoStorage(database_session_manager=session)
    publisher = NatsPublisher()
    apscheduler = initialize_apscheduler()

    app.state.apschedular = apscheduler
    app.state.research_manager = initialize_research_manager(publisher=publisher, repository=repository)

    app.state.analytic_collector = AnalyticCollector
    app.state.publisher = publisher
    app.state.db_session = session
    app.state.repository = repository
    logger.info("Initialized classes")
    yield

    # Закрытие ресурсов (если необходимо)
    logger.info("Cleanup after lifespan")
    apscheduler.shutdown()


def create_server(lifespan_func=lifespan):
    server = FastAPI(
        lifespan=lifespan_func,
        title="APPLICATION",
    )
    server.include_router(research_router)
    server.include_router(client_router)
    server.include_router(dialog_router)
    server.include_router(configuration_router)
    # Путь к директории для статических файлов
    static_directory_path = "static"

    # Проверка и создание директории, если она не существует
    if not os.path.exists(static_directory_path):
        os.makedirs(static_directory_path)
        print(f"Directory {static_directory_path} was created.")

    # Подключение директории статических файлов
    server.mount("/static", StaticFiles(directory=static_directory_path), name="static")
    return server
