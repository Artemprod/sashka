import asyncio
import uuid
from random import randint

from faststream.nats import NatsBroker

from src.telegram_client.client.model import ClientConfigDTO

# client_configs = ClientConfigDTO(
#         name="test",
#         api_id="17349",
#         api_hash="344583e45741c457fe1862106095a5eb",
#         phone_number="9996609358",
#         password='89671106966',
#         test_mode=True,
#     )

async def pub():
    async with NatsBroker() as broker:
        client_configs = ClientConfigDTO(
            name=f"test_{uuid.uuid4()}",
            api_id="17349",
            api_hash="344583e45741c457fe1862106095a5eb",
            phone_number=f"999660{randint(1000, 9999)}",
            password='89671106966',
            test_mode=True,
            parse_mode='markdown'
        )
        await broker.publish(client_configs.to_dict(), subject="create_clietn")




asyncio.run(pub())
