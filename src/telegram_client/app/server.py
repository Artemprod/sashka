import websockets
import asyncio
from loguru import logger
from pyrogram import Client

import asyncio

from pyrogram import Client, idle
from pyrogram.handlers import MessageHandler
from loguru import logger



async def start_client():
    async with websockets.serve(handler, '', 8001):
        client = Client(name=name, api_id=test_api_id,
                        api_hash=test_api_hash,
                        phone_number=test_phone,
                        password=test_password,
                        test_mode=True)

        client.add_handler(MessageHandler(get_income_message))
        asyncio.create_task(listen_command(client=client))

        await client.start()
        await idle()
        await asyncio.Future()


async def main():
    logger.info("Server start ")
    await start_client()


if __name__ == '__main__':
    asyncio.run(main())
