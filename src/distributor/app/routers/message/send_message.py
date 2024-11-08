import json
from typing import Optional
from datetime import datetime, timezone

from loguru import logger
from faststream import Context, Depends
from faststream.nats import NatsRouter, NatsMessage, JStream
from pydantic import BaseModel
from pyrogram import Client
from pyrogram.errors import PeerIdInvalid
from telethon import TelegramClient

from src.distributor.app.dependency.message import _get_data_from_headers
from src.distributor.app.routers.parse.gather_info import UserDTOBase
from src.distributor.app.schemas.message import Datas
from src.distributor.app.utils.message import send_message
from src.distributor.exceptions.atribute import UsernameError
from src.distributor.exceptions.messeage import FirstSendMessageError
from src.distributor.telegram_client.pyro.client.container import ClientsManager

from nats.js.api import DeliverPolicy, RetentionPolicy

# Создаем маршрутизатор NATS и две очереди JStream
router = NatsRouter()



@router.subscriber(stream=JStream(name="WORK_QUEUE_4", retention=RetentionPolicy.WORK_QUEUE),
                   subject="test_4.messages.send.first", deliver_policy=DeliverPolicy.ALL, no_ack=True)
async def send_first_message_subscriber(body: str, msg: NatsMessage, context=Context(),
                                        data: Datas = Depends(_get_data_from_headers)):

    """Send the first message with delay"""

    if data.current_time < data.send_time:
        delay = (data.send_time - data.current_time).total_seconds()
        await msg.nack(delay=delay)
        logger.info(f"Message {data.user, body}  delayed for {delay} ")
    else:
        try:
            msg_data = await send_message(data.client, data.user, body)
            logger.info(f"Message sent at {data.current_time}: {msg_data}")
            await msg.ack()
        except Exception as e:
            logger.error(f"Error while sending message: {e}")


@router.subscriber(stream=JStream(name="CONVERSATION", retention=RetentionPolicy.WORK_QUEUE),
                   subject="test.message.conversation.send", deliver_policy=DeliverPolicy.ALL,
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
        await msg.nack()
