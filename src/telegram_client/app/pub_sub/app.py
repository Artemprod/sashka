import asyncio

from faststream import FastStream, ContextRepo, context, Context
from faststream.nats import NatsBroker
from pyrogram import Client

from src.dispatcher.communicators.reggestry import ConsoleCommunicator
from src.telegram_client.app.app_manager import Manager
from src.telegram_client.app.model import ClientConfigDTO
from src.telegram_client.app.pub_sub.subscriber import router


async def main():
    """Запускает faststream и создает корутину для клиента"""
    client_configs = ClientConfigDTO(
        name="test",
        api_id="17349",
        api_hash="344583e45741c457fe1862106095a5eb",
        phone_number="9996609358",
        password='89671106966',
        test_mode=True,
    )

    manager = Manager(
        client=Client(**client_configs.to_dict()),
        plug=dict(root=r"D:\projects\AIPO_V2\CUSTDEVER\src\telegram_client\plugins")
    )

    broker = NatsBroker()
    broker.include_router(router)
    context.set_global("client", manager.app)
    app = FastStream(broker=broker)
    asyncio.create_task(manager.run(communicator=ConsoleCommunicator()))
    await app.run()
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
