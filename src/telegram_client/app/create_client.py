# Основным приложением является брокер сообщений
# Брокер сообщений запущен в цикле собтыий
# при запуске инициализируетя хранилище клиентов
# Клиент добовляется в хранилище


import asyncio
from contextlib import asynccontextmanager

from faststream import FastStream, ContextRepo
from faststream.nats import NatsBroker

from src.telegram_client.client.container import ClientsManager
from src.database.database_t import database
from src.telegram_client.app.routers.handler_clietn import client_router
from src.database.connections.redis_connect import RedisClient


@asynccontextmanager
async def lifespan(context: ContextRepo):
    container = ClientsManager(database=database,redis_client=RedisClient())
    context.set_global("container", container)
    yield



async def main():
    """Запускает faststream и создает корутину для клиента"""
    broker = NatsBroker()
    broker.include_router(client_router)
    app = FastStream(broker=broker, lifespan=lifespan)
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
