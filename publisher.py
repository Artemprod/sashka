import asyncio
import uuid
from random import randint

from faststream.nats import NatsBroker
from pyrogram.enums import ParseMode

from src.distributor.telegram_client.device_configs import iPhoneX, GooglePixel5
from src.distributor.telegram_client.pyro.client.model import ClientConfigDTO
from src.distributor.telegram_client.pyro.te_cli_ import MyClient



API_ID = "23823287"
API_HASH = "fe561473a06737cb358db923e05e7868"


# client_configs = ClientConfigDTO(
#         name="test",
#         api_id="17349",
#         api_hash="344583e45741c457fe1862106095a5eb",
#         phone_number="9996609358",
#         password='89671106966',
#         test_mode=True,
#     )

async def pub_test_server():
    async with NatsBroker() as broker:
        client_configs = ClientConfigDTO(
            name=f"test_{uuid.uuid4()}",
            api_id="17349",
            api_hash="344583e45741c457fe1862106095a5eb",
            phone_number=f"999660{randint(1111, 9999)}",
            password='89671106966',
            test_mode=True,
            parse_mode='markdown'
        )
        await broker.publish(client_configs.to_dict(), subject="create_clietn")


async def pub():
    async with NatsBroker() as broker:
        client_configs = ClientConfigDTO(
            name=f"test",
            app_version=GooglePixel5.app_version,
            device_model=GooglePixel5.device_model,
            system_version="4.16.30-vxCUSTOM",
            api_id=API_ID,
            api_hash=API_HASH,
            test_mode=False,
            phone_number="573175306617",
            password='7532',
            parse_mode=ParseMode.MARKDOWN.value,
        )
        await broker.publish(client_configs.to_dict(), subject="client.telethon.create")


if __name__ == '__main__':
    async def main():
        client = MyClient(name=f"Original_servere_accaunt_1",
                          api_id=API_ID,
                          api_hash=API_HASH,
                          test_mode=False,
                          phone_number=f"+79185184994",
                          password='',
                          parse_mode=ParseMode.MARKDOWN.value,
                          plugins=None
                          )
        await client.start()


    asyncio.run(pub())
