# Основным приложением является брокер сообщений
# Брокер сообщений запущен в цикле собтыий
# при запуске инициализируетя хранилище клиентов
# Клиент добовляется в хранилище


import asyncio
from contextlib import asynccontextmanager

from faststream import FastStream, ContextRepo, context, Context
from faststream.nats import NatsBroker

from src.telegram_client.create_client_event.container import ClientContainer
from src.telegram_client.create_client_event.handler_clietn import client_router





@asynccontextmanager
async def lifespan(context: ContextRepo):
    container = ClientContainer()
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
