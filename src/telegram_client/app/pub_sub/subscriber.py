from loguru import logger

from faststream import Context
from faststream.nats import NatsRouter
from pyrogram import Client

router = NatsRouter()


@router.subscriber("test_send_message", )
async def send_m(message, context=Context()):

    """Слушает очередь на отправку сообщения клиентом в телеграм, клиент передается контекстом"""
    client: Client = context.get("client")
    user = await client.get_chat('testing_test_tes')
    if client:
        await client.send_message(user.id, text=message)
        # logger.info("Message sent")
    else:
        logger.error("Client not found in context")