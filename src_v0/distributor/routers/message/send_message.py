import ast
from typing import List, Optional

from loguru import logger
from nats.js.api import DeliverPolicy, RetentionPolicy
from datetime import datetime, timezone
from faststream import Context, Depends
from faststream.nats import NatsRouter, NatsMessage, JStream
from pydantic import BaseModel, Field
from pyrogram import Client
from pyrogram.errors import PeerIdInvalid

from src_v0.telegram_client.client.container import ClientsManager

router = NatsRouter()

stream = JStream(name="WORK_QUEUE_4", retention=RetentionPolicy.WORK_QUEUE)
stream_2 = JStream(name="CONVERSATION", retention=RetentionPolicy.WORK_QUEUE)


class NatsHeaders(BaseModel):
    class Config:
        allow_population_by_field_name = True
        from_attributes = True  # Assuming this is here for a reason, otherwise it can be removed.


class UserDTOBase(BaseModel):
    name: Optional[str] = None
    tg_user_id: Optional[int] = None
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class TelegramTimeDelaHeadersDTO(NatsHeaders):
    tg_client_name: str
    users: str  # Consider type hinting the expected format, e.g., `List[str]` if it's a delimited string.
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


async def derive_data(msg: NatsMessage, context=Context()) -> Datas:
    user = _extract_user_from_headers(msg.headers)
    client_name = msg.headers.get("tg_client_name")
    if not client_name:
        logger.error("Missing client name in headers.")
        raise ValueError("Missing client name in headers.")

    container: ClientsManager = context.get("container")
    client: Client = container.get_client_by_name(name=client_name)
    current_time = datetime.now(tz=timezone.utc)
    send_time = datetime.fromtimestamp(
        float(msg.headers.get('send_time_next_message_timestamp', current_time.timestamp())),
        tz=timezone.utc
    )

    logger.debug(f"Derived data: {user}, {client_name}, {current_time}, {send_time}")

    return Datas(
        user=user,
        client_name=client_name,
        client=client,
        container=container,
        current_time=current_time,
        send_time=send_time,
    )


def _extract_user_from_headers(headers) -> UserDTOBase:
    user_dict = headers.get("user")
    if isinstance(user_dict, dict):
        return UserDTOBase(**user_dict)
    logger.error("Invalid user header format.")
    raise ValueError("Invalid user header format.")


async def send_message(client: Client, user: UserDTOBase, body: str):
    try:
        return await client.send_message(user.name, text=body)
    except PeerIdInvalid:
        logger.warning("PeerIdInvalid: Trying to send by ID.")
        return await client.send_message(user.tg_user_id, text=body)


@router.subscriber(stream=stream, subject="test_4.messages.send.first", deliver_policy=DeliverPolicy.ALL, no_ack=True)
async def send_first_message(body: str, msg: NatsMessage, context=Context(), data: Datas = Depends(derive_data)):
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

#_____________________________________________________________________

async def extract_message_data(msg: NatsMessage, context=Context()):
    """Extract and validate necessary data from the message headers."""
    logger.debug("Extracting data from headers.")

    tg_client_name = msg.headers.get("tg_client_name")
    tg_user_user_id = msg.headers.get('tg_user_user_id')

    if not tg_client_name:
        logger.error("Missing 'tg_client_name' in headers.")
        raise ValueError("Missing 'tg_client_name' in headers.")

    try:
        tg_user_user_id = int(tg_user_user_id)
    except (TypeError, ValueError) as e:
        logger.error(f"Invalid 'tg_user_user_id': {e}")
        raise ValueError("Invalid 'tg_user_user_id' in headers.")

    container: ClientsManager = context.get("container")
    client: Client = container.get_client_by_name(name=tg_client_name)

    return client, tg_user_user_id


@router.subscriber(stream=stream_2,subject="test.message.conversation.send",
                   deliver_policy=DeliverPolicy.ALL, no_ack=True)
async def send_message(
        body: str,
        msg: NatsMessage,
        context=Context(),
        data=Depends(extract_message_data)
):
    """Send a message."""
    client, tg_user_user_id = data

    logger.info("Sending message...")

    try:
        msg_data = await client.send_message(tg_user_user_id, text=body)
        logger.info(f"Message sent: {msg_data}")
        await msg.ack()
    except PeerIdInvalid:
        logger.error(f"Invalid user ID: {tg_user_user_id}")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
