from faststream import Context
from faststream.nats import NatsRouter
from pyrogram import Client

from src.dispatcher.communicators.reggestry import ConsoleCommunicator
from src.telegram_client.client.model import ClientConfigDTO
from src.telegram_client.client.roters.new_income_message.answer_mesg_router import answ_router
from src.telegram_client.client.container import ClientsManager

client_router = NatsRouter()



# def create_manager(client_configs: dict) -> Manager:
#     client = Client(**client_configs)
#     manager = Manager(client=client)
#     manager.include_router(answ_router)
#     return manager



@client_router.subscriber("create_clietn", )
async def create_client(message, context=Context()):
    """Инициализирует клиента и запускает его в лупе"""
    container: ClientsManager = context.get("container")
    # Парсинг и валидация данных
    # Делегирую создание клиента
    client_configs = message
    dto = ClientConfigDTO(**client_configs)
    # manager: Manager = create_manager(dto.to_dict())
    # тут возможно какато валидация или доа логика
    await container.create_client_connection(client_configs=dto, routers=[answ_router], communicator=ConsoleCommunicator())
    print(container.managers)



@client_router.subscriber("send_message", )
async def send_message(message, context=Context()):
    """Инициализирует клиента и запускает его в лупе"""
    container: ClientsManager = context.get("container")
    # Парсинг и валидация данных
    # Делегирую создание клиента
    client: Client = container.get_client_by_name(name=message["client_id"])
    mesage = message['text']
    print(mesage)
    user = await client.get_chat("aitestings")
    msg_data = await client.send_message(user.id, text=mesage)
    print(msg_data)
