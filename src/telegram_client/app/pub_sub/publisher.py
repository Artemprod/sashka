import asyncio

from faststream.nats import NatsBroker


async def pub():
    async with NatsBroker() as broker:
        await broker.publish("Это из NATS", subject="test_send_message")


asyncio.run(pub())
