import asyncio

from faststream import Context
from faststream.nats import NatsRouter

from src.distributor.telegram_client.pyro.client.container import ClientsManager
from src.distributor.telegram_client.pyro.client.model import ClientConfigDTO




from src.dispatcher.communicators.reggestry import ConsoleCommunicator
from src.distributor.telegram_client.pyro.client.roters.message.router import answ_router
from src.distributor.telegram_client.telethoncl.manager.container import TelethonClientsContainer

router = NatsRouter()


# @router.subscriber("client.pyrogram.create", )
# async def create_client(message, context=Context()):
#     """Инициализирует клиента и запускает его"""
#
#     container: ClientsManager = context.get("pyrogram_container")
#     dto = ClientConfigDTO(**message)
#     container.routers = [answ_router]
#     task = asyncio.create_task(container.create_client_connection(client_configs=dto, communicator=ConsoleCommunicator()))
#     try:
#         await task
#     except Exception as e:
#         raise

@router.subscriber("client.telethon.create", )
async def create_telethon_client(message, context=Context()):
    """Инициализирует клиента и запускает его"""

    container:TelethonClientsContainer = context.get("telethon_container")
    dto = ClientConfigDTO(**message)
    task = asyncio.create_task(container.create_and_start_client(client_configs=dto,communicator=ConsoleCommunicator()))
    try:
        await task
    except Exception as e:
        raise

   
