from datetime import datetime, timezone

from faststream import Context
from faststream.nats import NatsRouter, NatsBroker, NatsMessage, JStream
from nats.js.api import DeliverPolicy, RetentionPolicy, AckPolicy
from pyrogram import Client

from src.dispatcher.communicators.reggestry import ConsoleCommunicator
from src.resrcher.models import QUEUEMessage
from src.telegram_client.client.model import ClientConfigDTO
# from src.telegram_client.client.roters.new_income_message.answer_mesg_router import answ_router
from src.telegram_client.client.container import ClientsManager

stream = JStream(name="WORK_QUEUE_4", retention=RetentionPolicy.WORK_QUEUE)
client_router = NatsRouter()


# @client_router.subscriber("create_clietn", )
# async def create_client(message, context=Context()):
#     """Инициализирует клиента и запускает его в лупе"""
#     container: ClientsManager = context.get("container")
#     # Парсинг и валидация данных
#     # Делегирую создание клиента
#     client_configs = message
#     dto = ClientConfigDTO(**client_configs)
#     # manager: Manager = create_manager(dto.to_dict())
#     # тут возможно какато валидация или доа логика
#     container.routers = [answ_router]
#     await container.create_client_connection(client_configs=dto, communicator=ConsoleCommunicator())
#     print(container.managers)
#     async with NatsBroker() as broker:
#         message = client_configs
#         await broker.publish(message, subject="save_client")


@client_router.subscriber(stream=stream, subject="test_4.messages.send.first", deliver_policy=DeliverPolicy.ALL, no_ack=True)
async def send_first_message(body: str, msg:NatsMessage , context=Context()):
    """отправляет сообщение """

    current_time = datetime.now(tz=timezone.utc)
    send_time = datetime.fromtimestamp(
        float(msg.headers.get('SendTime-Next-Message-Timestamp', datetime.now(tz=timezone.utc).timestamp())),
        tz=timezone.utc
    )
    user_id = msg.headers.get('Tg-User-UserId')
    if current_time < send_time:
        nack_delay = float((send_time - current_time).total_seconds())
        await msg.nack(delay=nack_delay)
    else:
        client = msg.headers.get('Tg-Client-Name', None)
        print("MESSAGE:",body )
        print(f"MESAGE SEND___________ time {current_time}` message {msg}`  send to client telegram")
        print(f'USER ID: {user_id}')
        await msg.ack()


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
