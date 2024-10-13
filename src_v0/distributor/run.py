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

from src.telegram_client.client.container import ClientsManager
from src.telegram_client.client.roters.message.router import answ_router
from src_v0.database.postgres.engine.session import DatabaseSessionManager
from src_v0.database.repository.storage import RepoStorage
from src_v0.distributor.routers.databse.database import database_router
from src_v0.distributor.routers.message.new_massage import handle_message_router
from src_v0.distributor.routers.message.send_message import router
from src_v0.distributor.routers.parse.gather_info import parser_router
from src_v0.distributor.routers.reserch.reserch import reserch_router

from src_v0.distributor.routers.client.handler_clietn import client_router
from src_v0.database.connections.redis_connect import RedisClient


env = Env()
env.read_env('.env')
dev_mode = env("DEV_MODE") == "true"
sys.path.append(str(Path(__file__).parent.parent))


@asynccontextmanager
async def lifespan(context: ContextRepo):
    repository: RepoStorage = RepoStorage(DatabaseSessionManager(database_url=env("DATABASE_URL")))
    redis_connection_manager: RedisClient = RedisClient()
    container = ClientsManager(repository=repository, redis_connection_manager=redis_connection_manager,
                               routers=[answ_router], dev_mode=dev_mode)
    await container.start()
    context.set_global("container", container)
    context.set_global("repository", repository)
    context.set_global("redis_connection_manager", redis_connection_manager)
    yield


async def main():
    """Запускает faststream и создает корутину для клиента"""
    broker = NatsBroker("nats://localhost:4222")
    broker.include_router(client_router)
    broker.include_router(router)
    broker.include_router(database_router)
    broker.include_router(handle_message_router)
    broker.include_router(reserch_router)
    broker.include_router(parser_router)
    app = FastStream(broker=broker, lifespan=lifespan)
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
