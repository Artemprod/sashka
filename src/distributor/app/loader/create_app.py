import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from environs import Env
from faststream import FastStream, ContextRepo
from faststream.nats import NatsBroker
from loguru import logger

from src.database.connections.redis_connect import RedisClient
from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.repository.storage import RepoStorage
from src.distributor.app.loader.on_startup import initialize_telethon_container, initialize_pyrogram_container
from src.distributor.app.routers.client.client import router as client_router
from src.distributor.app.routers.message.send_message import router as message_router
from src.distributor.app.routers.parse.gather_info import router as parse_router
from src.distributor.telegram_client.telethoncl.manager.container import TelethonClientsContainer

env = Env()
env.read_env('.env')
dev_mode = env("DEV_MODE") == "true"
sys.path.append(str(Path(__file__).parent.parent))


@asynccontextmanager
async def lifespan(context: ContextRepo):
    repository = RepoStorage(database_session_manager=DatabaseSessionManager(
        database_url=env("DATABASE_URL")))
    redis_connection_manager: RedisClient = RedisClient()
    telethon_container:TelethonClientsContainer = initialize_telethon_container(repository=repository)
    pyrogram_container = initialize_pyrogram_container(repository=repository,
                                                       redis_connection_manager=redis_connection_manager)

    context.set_global("telethon_container", telethon_container)
    context.set_global("pyrogram_container", pyrogram_container)
    logger.info("app has been startup")
    client_task = asyncio.create_task(telethon_container.start_all_clients())
    logger.info(f"clients started {client_task}")
    yield
    logger.warning("App distribute is shouting down")


def create_app():
    """Запускает faststream и создает корутину для клиента"""
    broker = NatsBroker(env("NATS_SERVER"))

    broker.include_router(client_router)
    broker.include_router(message_router)
    broker.include_router(parse_router)

    app = FastStream(broker=broker, lifespan=lifespan, title="CLIENT DISTRIBUTE")
    return app
