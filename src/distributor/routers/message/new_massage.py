from faststream import Context
from faststream.nats import NatsRouter, NatsBroker

handle_message_router = NatsRouter()

reserch = {}
@handle_message_router.subscriber("new_message")
async def distribute_message(message, context=Context()):
    """Распределяет сообщени по их назначению"""
    print(message)
    print('эмитация отправки в базу ')
    reserch['name'] = 'test'
    reserch['users'] = [123,432,123]

    # Тут определить есть ли пользователь в иследовании если есть то отдать асистенат котрый закреплен за иследованием если нет то который просто общается
    # сгенерировать ответ
    # Дернуть ручку которая отвечает за послание сообщения fastapi
    async with NatsBroker() as broker:
        message = {'client_id': message['client'], "text": "это вот из клиента через очередь которая по кругу которая управляет распределением сообщений"}
        await broker.publish(message, subject="send_message")


