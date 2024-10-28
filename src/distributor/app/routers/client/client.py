import asyncio
import json

from faststream import Context
from faststream.nats import NatsRouter

from src.dispatcher.dispatcher import CommunicatorDispatcher
from src.distributor.app.schemas.singup import TelegramServiceClientSignupDTO
from src.distributor.telegram_client.pyro.client.container import ClientsManager
from src.distributor.telegram_client.pyro.client.model import ClientConfigDTO

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
    print(message)
    container: TelethonClientsContainer = context.get("telethon_container")
    converted_message = json.loads(message)
    service_dto = TelegramServiceClientSignupDTO(**converted_message)
    service_type = service_dto.service_type
    client_dto = ClientConfigDTO(**service_dto.client_config.to_dict())
    # Создаем коммуникатор с внешним сервисом в зависимости от типа сервиса ( использую диспетчеризацию)
    #todo сделать присвоение атрибутов к комуникатору
    #todo сделать передовать распокованый словарь в метод чтобы сджелать более адаптивным
    communicator = CommunicatorDispatcher(service_name=service_type).get_communicator(user_id=service_dto.service_data.user_id)
    task = asyncio.create_task(container.create_and_start_client(client_configs=client_dto, communicator=communicator))
    try:
        await task
    except Exception as e:
        raise
