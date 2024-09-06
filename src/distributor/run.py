# Основным приложением является брокер сообщений
# Брокер сообщений запущен в цикле собтыий
# при запуске инициализируетя хранилище клиентов
# Клиент добовляется в хранилище


import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from environs import Env
from faststream import FastStream, ContextRepo
from faststream.nats import NatsBroker

from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.repository.storage import RepoStorage
from src.distributor.routers.databse.database import database_router
from src.distributor.routers.message.new_massage import handle_message_router
from src.distributor.routers.reserch.reserch import reserch_router
from src.telegram_client.client.container import ClientsManager
from src.distributor.routers.client.handler_clietn import client_router
from src.database.connections.redis_connect import RedisClient

env = Env()
env.read_env('.env')
sys.path.append(str(Path(__file__).parent.parent))

@asynccontextmanager
async def lifespan(context: ContextRepo):
    repository: RepoStorage = RepoStorage(DatabaseSessionManager(database_url=env("DATABASE_URL")))
    redis_connection_manager: RedisClient = RedisClient()
    container = ClientsManager(repository=repository, redis_connection_manager=redis_connection_manager)
    await container.start()

    context.set_global("container", container)
    context.set_global("repository", repository)
    context.set_global("redis_connection_manager", redis_connection_manager)
    yield


async def main():
    """Запускает faststream и создает корутину для клиента"""
    broker = NatsBroker()
    broker.include_router(client_router)
    broker.include_router(database_router)
    broker.include_router(handle_message_router)
    broker.include_router(reserch_router)
    app = FastStream(broker=broker, lifespan=lifespan)
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
