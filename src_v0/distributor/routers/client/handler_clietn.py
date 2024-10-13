import asyncio
from datetime import datetime, timezone

from faststream import Context
from faststream.nats import NatsRouter, NatsBroker, NatsMessage, JStream

from pydantic import BaseModel
from pyrogram import Client

from src.telegram_client.client.container import ClientsManager
from src.telegram_client.client.model import ClientConfigDTO
from src.telegram_client.client.roters.message.router import answ_router
from src_v0.dispatcher.communicators.reggestry import ConsoleCommunicator






client_router = NatsRouter()






@client_router.subscriber("create_clietn", )
async def create_client(message, context=Context()):
    """Инициализирует клиента и запускает его"""

    container: ClientsManager = context.get("container")
    dto = ClientConfigDTO(**message)
    container.routers = [answ_router]
    await container.create_client_connection(client_configs=dto, communicator=ConsoleCommunicator())
    print(container.managers)
    # await message.ack()

