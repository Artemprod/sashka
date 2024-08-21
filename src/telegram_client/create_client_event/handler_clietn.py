import asyncio
import uuid

from loguru import logger

from faststream import Context
from faststream.nats import NatsRouter
from pyrogram import Client

from src.dispatcher.communicators.reggestry import ConsoleCommunicator
from src.telegram_client.app.app_manager import Manager
from src.telegram_client.app.model import ClientConfigDTO
from src.telegram_client.create_client_event.answer_mesg_router import answ_router
from src.telegram_client.create_client_event.container import ClientContainer
from src.telegram_client.create_client_event.pyro_router import Router

client_router = NatsRouter()



def create_manager(client_configs: dict) -> Manager:
    client = Client(**client_configs)
    manager = Manager(client=client)
    manager.include_router(answ_router)
    return manager



@client_router.subscriber("create_clietn", )
async def create_client(message, context=Context()):
    """Инициализирует клиента и запускает его в лупе"""
    container: ClientContainer = context.get("container")
    # Парсинг и валидация данных
    # Делегирую создание клиента
    client_configs = message
    dto = ClientConfigDTO(**client_configs)
    manager: Manager = create_manager(dto.to_dict())
    # тут возможно какато валидация или доа логика
    asyncio.create_task(manager.run(communicator=ConsoleCommunicator()))
    container.add_client(client=manager.app, name=str(uuid.uuid4()))
    print(container.clients)



@client_router.subscriber("send_message", )
async def send_message(message, context=Context()):
    """Инициализирует клиента и запускает его в лупе"""
    container: ClientContainer = context.get("container")
    # Парсинг и валидация данных
    # Делегирую создание клиента
    client: Client = container.get_client(message["client_id"])
    mesage = message['text']
    print(mesage)
    user = await client.get_chat("aitestings")
    msg_data = await client.send_message(user.id, text=mesage)
    print(msg_data)
