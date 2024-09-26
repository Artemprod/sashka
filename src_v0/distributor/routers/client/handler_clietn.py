from datetime import datetime, timezone

from faststream import Context
from faststream.nats import NatsRouter, NatsBroker, NatsMessage, JStream
from nats.js.api import DeliverPolicy, RetentionPolicy, AckPolicy
from pyrogram import Client

from src_v0.dispatcher.communicators.reggestry import ConsoleCommunicator
from src_v0.resrcher.models import QUEUEMessage
from src_v0.telegram_client.client.model import ClientConfigDTO
# from src.telegram_client.client.roters.new_income_message.answer_mesg_router import answ_router
from src_v0.telegram_client.client.container import ClientsManager
from src_v0.telegram_client.client.roters.new_income_message.answer_mesg_router import answ_router

stream = JStream(name="WORK_QUEUE_4", retention=RetentionPolicy.WORK_QUEUE)
stream_2 = JStream(name="CONVERSATION", retention=RetentionPolicy.WORK_QUEUE)
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


@client_router.subscriber(stream=stream, subject="test_4.messages.send.first", deliver_policy=DeliverPolicy.ALL, no_ack=True)
async def send_first_message(body: str, msg:NatsMessage , context=Context()):
    """отправляет сообщение """
    container: ClientsManager = context.get("container")
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
        client: Client = container.get_client_by_name(name="test_e85d412a-bb82-4271-8197-1b3a284ed647")
        user = await client.get_chat("testing_test_tes")
        msg_data = await client.send_message(user.id, text=body)
        await msg.ack()


@client_router.subscriber(stream=stream_2, subject="test.message.conversation.send", deliver_policy=DeliverPolicy.ALL, no_ack=True)
async def send_message(body: str, msg:NatsMessage , context=Context()):
    """отправляет сообщение """
    container: ClientsManager = context.get("container")
    # # Парсинг и валидация данных
    # # Делегирую создание клиента
    client: Client = container.get_client_by_name(name="test_e85d412a-bb82-4271-8197-1b3a284ed647")
    user = await client.get_chat("testing_test_tes")
    msg_data = await client.send_message(user.id, text=body)
    print(body)
    await msg.ack()
