import asyncio

from faststream.nats import NatsBroker


async def pub():
    async with NatsBroker() as broker:
        message = {'client_id':"f3dde1", "text":"это вот из клиента"}
        await broker.publish(message, subject="send_message")

asyncio.run(pub())