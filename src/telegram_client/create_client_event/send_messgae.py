import asyncio

from faststream.nats import NatsBroker


async def pub():
    async with NatsBroker() as broker:
        message = {'client_id':'a00825f9-b88f-4b47-9a96-7d4600585686', "text":"это вот из клиента"}
        await broker.publish(message, subject="send_message")

asyncio.run(pub())