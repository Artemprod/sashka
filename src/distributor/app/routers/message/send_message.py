import asyncio
from typing import Optional

from faststream import Context
from faststream import Depends
from faststream.nats import JStream
from faststream.nats import NatsMessage
from faststream.nats import NatsRouter
from loguru import logger
from nats.js.api import DeliverPolicy
from nats.js.api import RetentionPolicy
from telethon.tl import types

from configs.nats_queues import nats_distributor_settings
from telethon import TelegramClient
from src.distributor.app.dependency.message import _get_data_from_headers, get_telegram_client, get_data_from_body
from src.distributor.app.schemas.message import Datas, MessageToSendData
from src.distributor.app.utils.message import send_message, send_message_with_typing

# Создаем маршрутизатор NATS и две очереди JStream
router = NatsRouter()


@router.subscriber(
    stream=JStream(
        name=nats_distributor_settings.message.first_message_message.stream, retention=RetentionPolicy.WORK_QUEUE
    ),
    subject=nats_distributor_settings.message.first_message_message.subject,
    deliver_policy=DeliverPolicy.ALL,
    no_ack=True,
)
async def send_first_message_subscriber(
    body: str, msg: NatsMessage, context=Context(), data: Datas = Depends(_get_data_from_headers)
):
    """Send the first message with delay"""

    if data.current_time < data.send_time:
        delay = (data.send_time - data.current_time).total_seconds()
        await msg.nack(delay=delay)
        logger.info(f"Message {data.user, body}  delayed for {delay} ")
    else:
        try:
            await msg.ack()
            msg_data = await send_message(data.client, data.user, message=body)
            logger.info(f"Message sent at {data.current_time}: {msg_data}")
        except Exception as e:
            logger.error(f"Error while sending message: {e}")
            raise e




@router.subscriber(
    stream=JStream(name=nats_distributor_settings.message.send_message.stream, retention=RetentionPolicy.WORK_QUEUE),
    subject=nats_distributor_settings.message.send_message.subject,
    deliver_policy=DeliverPolicy.ALL,
    no_ack=True,
)
async def send_message_subscriber(
        body: str,
        msg: NatsMessage,
        context: Context = Context(),
        data: Optional[MessageToSendData] = Depends(get_data_from_body),
        client: TelegramClient = Depends(get_telegram_client),
) -> None:
    """
    Создает неблокирующую задачу для отправки сообщения.
    Мгновенно возвращает управление, позволяя параллельную обработку множества сообщений.
    """
    message_id = getattr(data, 'message_id', 'unknown')

    # Подтверждаем получение сообщения
    await msg.ack()
    logger.info(f"Message {message_id} acknowledged")

    if not data or not data.message:
        logger.warning("No message content to send, skipping")
        return

    async def handle_send_task():
        try:
            result = await send_message_with_typing(
                client=client,
                user=data.user,
                message=data.message
            )

            if isinstance(result, types.Message):
                logger.info(
                    f"Message {message_id} sent successfully to user {data.user.tg_user_id}. "
                    f"Telegram message ID: {result.id}"
                )
            else:
                logger.warning(
                    f"Message {message_id} sent, but returned unexpected result type: {type(result)}"
                )

        except Exception as e:
            logger.error(
                f"Failed to send message {message_id}: {str(e)}",
                exc_info=True,
                extra={
                    "user_id": getattr(data, 'user', {}).get('tg_user_id', 'unknown'),
                    "message_id": message_id
                }
            )

    # Создаем задачу и сразу возвращаем управление
    asyncio.create_task(
        handle_send_task(),
        name=f"send_message_{message_id}"
    )

    logger.info(f"Created send task for message {message_id}")



#
# @router.subscriber(
#     stream=JStream(name=nats_distributor_settings.message.send_message.stream, retention=RetentionPolicy.WORK_QUEUE),
#     subject=nats_distributor_settings.message.send_message.subject,
#     deliver_policy=DeliverPolicy.ALL,
#     no_ack=True,
# )
# async def send_message_subscriber(
#     body: str,
#     msg: NatsMessage,
#     context=Context(),
#     data=Depends(get_data_from_body),
#     client=Depends(get_telegram_client),
# ):
#     """Send a conversation message."""
#     await msg.ack()
#     logger.warning("message acked")
#     try:
#         logger.info("Sending message...")
#         if not data.message:
#             logger.warning(f"There is no message to send, i will not send anything")
#         else:
#             send_task = asyncio.create_task(send_message_with_typing(client=client, user=data.user, message=data.message),
#                                             name=f"send_message_{getattr(data, 'message_id', 'unknown')}")
#             logger.info(f"Message sent task: {send_task}")
#
#     except Exception as e:
#         logger.error(f"Failed to send message: {e}")
#         raise e