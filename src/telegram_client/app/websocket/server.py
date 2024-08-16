import websockets
import asyncio
from pyrogram import Client
from loguru import logger
from src.dispatcher.communicators.reggestry import ConsoleCommunicator
from src.telegram_client.app.app_manager import Manager
from src.telegram_client.app.model import ClientConfigDTO

command_queue = asyncio.Queue()
message_queue = asyncio.Queue()


async def publisher(websocket):
    """ Публикует входящие сообщения от лкиента в очередь
    происходит какая то предварительная обработка соообщений
    """
    while True:
        message = await websocket.recv()
        print(message)
        await command_queue.put(message)


async def listen_command(client: Client):
    """ Слушает очередь с командами и выаолняет команду у клиеньта"""
    while True:
        command = await command_queue.get()
        logger.info(f"get command {command}")
        if command == 'send_msg':

            await client.send_message(chat_id=client.me.id, text="привет")
            command_queue.task_done()
        else:
            logger.info(f"Wrong command {command}")
            command_queue.task_done()


async def start_client(client_configs: ClientConfigDTO):
    logger.info("Server start ")
    async with websockets.serve(publisher, '', 8002):

        client = Client(**client_configs.to_dict())
        manager = Manager(client=client, coro=listen_command)
        await manager.run(communicator=ConsoleCommunicator())
        await asyncio.Future()


async def main():
    client_configs = ClientConfigDTO(
        name="test",
        api_id="17349",
        api_hash="344583e45741c457fe1862106095a5eb",
        phone_number="9996601212",
        password='89671106966',
        test_mode=True,
        plugins=dict(root=r"D:\projects\AIPO_V2\CUSTDEVER\src\telegram_client\plugins")

    )

    await start_client(client_configs=client_configs)


if __name__ == '__main__':
    asyncio.run(main())
