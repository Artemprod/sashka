from faststream import Context
from faststream.nats import NatsRouter, NatsBroker
from pyrogram import Client

from src.dispatcher.communicators.reggestry import ConsoleCommunicator
from src.telegram_client.client.model import ClientConfigDTO
from src.telegram_client.client.roters.new_income_message.answer_mesg_router import answ_router
from src.telegram_client.client.container import ClientsManager

client_router = NatsRouter()


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
    container.routers = [answ_router]
    await container.create_client_connection(client_configs=dto, communicator=ConsoleCommunicator())
    print(container.managers)
    async with NatsBroker() as broker:
        message = client_configs
        await broker.publish(message, subject="save_client")


@client_router.subscriber("send_first_message", )
async def send_message(message, context=Context()):
    """отправляет сообщение """
    container: ClientsManager = context.get("container")
    # Парсинг и валидация данных
    # Делегирую создание клиента
    client: Client = container.get_client_by_name(name=message["client_id"])
    mesage = message['text']
    print(mesage)
    user = await client.get_chat("aitestings")
    msg_data = await client.send_message(user.id, text=mesage)
    print(msg_data)



# @client_router.subscriber("send_message", )
# async def send_message(message, context=Context()):
#     """отправляет сообщение """
#     container: ClientsManager = context.get("container")
#     # Парсинг и валидация данных
#     # Делегирую создание клиента
#     client: Client = container.get_client_by_name(name=message["client_id"])
#     mesage = message['text']
#     print(mesage)
#     user = await client.get_chat("aitestings")
#     msg_data = await client.send_message(user.id, text=mesage)
#     print(msg_data)
#
#
# @client_router.subscriber("send_message_from_reserch", )
# async def send_message(message, context=Context()):
#     """отправляет сообщение """
#     container: ClientsManager = context.get("container")
#     client: Client = container.get_client_by_name(name=message["client_id"])
#     mesage = message['text']
#     uer_id = int(message['uer_id'])
#     print(mesage)
#     msg_data = await client.send_message(uer_id, text=mesage)
#     print(msg_data)