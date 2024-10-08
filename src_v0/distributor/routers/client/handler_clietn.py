import asyncio
from datetime import datetime, timezone

from faststream import Context
from faststream.nats import NatsRouter, NatsBroker, NatsMessage, JStream

from pydantic import BaseModel
from pyrogram import Client

from src_v0.dispatcher.communicators.reggestry import ConsoleCommunicator

from src_v0.telegram_client.client.model import ClientConfigDTO

from src_v0.telegram_client.client.container import ClientsManager
from src_v0.telegram_client.client.roters.new_income_message.answer_mesg_router import answ_router



client_router = NatsRouter()





# TODO Если я делегирую сохранения в базе данных нового клеинта на менеджера ?
@client_router.subscriber("create_clietn", )
async def create_client(message, context=Context()):
    """Инициализирует клиента и запускает его"""

    container: ClientsManager = context.get("container")
    dto = ClientConfigDTO(**message)
    container.routers = [answ_router]
    await container.create_client_connection(client_configs=dto, communicator=ConsoleCommunicator())
    print(container.managers)
    # await message.ack()

