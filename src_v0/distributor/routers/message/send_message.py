import json
from typing import Optional
from datetime import datetime, timezone

from loguru import logger
from faststream import Context, Depends
from faststream.nats import NatsRouter, NatsMessage, JStream
from pydantic import BaseModel
from pyrogram import Client
from pyrogram.errors import PeerIdInvalid
from src_v0.telegram_client.client.container import ClientsManager
from nats.js.api import DeliverPolicy, RetentionPolicy

# Создаем маршрутизатор NATS и две очереди JStream
router = NatsRouter()

stream = JStream(name="WORK_QUEUE_4", retention=RetentionPolicy.WORK_QUEUE)
stream_2 = JStream(name="CONVERSATION", retention=RetentionPolicy.WORK_QUEUE)


# Определяем пользователи и заголовки через Pydantic
class NatsHeaders(BaseModel):
    class Config:
        allow_population_by_field_name = True
        from_attributes = True


class UserDTOBase(BaseModel):
    name: Optional[str] = None
    tg_user_id: Optional[int] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class TelegramTimeDelaHeadersDTO(NatsHeaders):
    tg_client_name: str
    users: str
    send_time_msg_timestamp: str
    send_time_next_message_timestamp: str


class Datas(BaseModel):
    user: UserDTOBase
    client_name: str
    client: Client
    container: ClientsManager
    current_time: datetime
    send_time: datetime

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


async def _extract_user_from_headers(headers) -> UserDTOBase:
    user_dict = json.loads(headers.get("user"))
    if isinstance(user_dict, dict):
        return UserDTOBase(**user_dict)
    logger.error("Invalid user header format.")
    raise ValueError("Invalid user header format.")


async def _get_data_from_headers(msg: NatsMessage, context=Context()) -> Datas:
    print(msg.headers)
    user = await _extract_user_from_headers(msg.headers)
    client_name = msg.headers.get("tg_client")
    if not client_name:
        logger.error("Missing client name in headers.")
        raise ValueError("Missing client name in headers.")

    container: ClientsManager = context.get("container")
    client: Client = container.get_client_by_name(name=client_name)

    current_time = datetime.now(tz=timezone.utc)
    send_time_timestamp = msg.headers.get('send_time_next_message_timestamp')
    send_time = datetime.fromtimestamp(
        float(send_time_timestamp) if send_time_timestamp else current_time.timestamp(),
        tz=timezone.utc
    )

    return Datas(
        user=user,
        client_name=client_name,
        client=client,
        container=container,
        current_time=current_time,
        send_time=send_time,
    )


async def send_message(client: Client, user: UserDTOBase, body: str):
    try:
        return await client.send_message(user.name, text=body)
    except PeerIdInvalid:
        logger.warning("PeerIdInvalid: Trying to send by ID.")
        return await client.send_message(user.tg_user_id, text=body)


@router.subscriber(stream=stream, subject="test_4.messages.send.first", deliver_policy=DeliverPolicy.ALL, no_ack=True)
async def send_first_message(body: str, msg: NatsMessage, context=Context(),
                             data: Datas = Depends(_get_data_from_headers)):
    """Send the first message with delay"""
    if data.current_time < data.send_time:
        delay = (data.send_time - data.current_time).total_seconds()
        await msg.nack(delay=delay)
    else:
        try:
            msg_data = await send_message(data.client, data.user, body)
            logger.info(f"Message sent at {data.current_time}: {msg_data}")
            await msg.ack()
        except Exception as e:
            logger.error(f"Error while sending message: {e}")


@router.subscriber(stream=stream_2, subject="test.message.conversation.send", deliver_policy=DeliverPolicy.ALL,
                   no_ack=True)
async def send_message_subscriber(body: str, msg: NatsMessage, context=Context(), data=Depends(_get_data_from_headers)):
    """Send a conversation message."""
    logger.info("Sending message...")

    try:
        msg_data = await send_message(data.client, data.user, body)
        logger.info(f"Message sent: {msg_data}")
        await msg.ack()
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
