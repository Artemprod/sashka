from faststream import Context
from faststream.nats import NatsRouter, NatsBroker, NatsMessage, JStream

from pyrogram import Client


from src_v0.telegram_client.client.container import ClientsManager



handle_message_router = NatsRouter()


# reserch = {}
# @handle_message_router.subscriber("new_message")
# async def distribute_message(message, context=Context()):
#     """Распределяет сообщени по их назначению"""
#     print(message)
#     print('эмитация отправки в базу ')
#     reserch['name'] = 'test'
#     reserch['users'] = [123,432,123]
#
#     # Тут определить есть ли пользователь в иследовании если есть то отдать асистенат котрый закреплен за иследованием если нет то который просто общается
#     # сгенерировать ответ
#     # Дернуть ручку которая отвечает за послание сообщения fastapi
#     async with NatsBroker() as broker:
#         message = {'client_id': message['client'], "text": "это вот из клиента через очередь которая по кругу которая управляет распределением сообщений"}
#         await broker.publish(message, subject="send_message")




@handle_message_router.subscriber(subject="send_message")
async def new_message_message(msg: NatsMessage, context=Context()):
    container: ClientsManager = context.get("container")
    # # Парсинг и валидация данных
    # # Делегирую создание клиента
    # client_name = msg.headers.get('Tg-Client-Name', None)
    client: Client = container.get_client_by_name(name="test_9410d195-7ff2-4640-8bf2-e20ac3ee76e3")
    user = await client.get_chat("test_ai")
    print(user)
    # # msg_data = await client.send_message(user.id, text=body)
    #
    # await msg.ack()
