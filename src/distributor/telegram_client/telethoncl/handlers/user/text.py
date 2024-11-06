import json
import logging
import os

from environs import Env
from faststream.nats import NatsBroker
from loguru import logger
from numpy.compat import unicode
from pydantic import ValidationError
from telethon import events, TelegramClient
from telethon.tl.types import  User


from src.distributor.telegram_client.telethoncl.filters.media import TextFilter
from src.distributor.telegram_client.telethoncl.filters.model import SourceType
from src.distributor.telegram_client.telethoncl.models.messages import OutcomeMessageDTOQueue
from src.schemas.service.queue import NatsQueueMessageDTOSubject
from src.services.publisher.publisher import NatsPublisher

env = Env()
env.read_env('.env')
publisher = NatsPublisher()


@events.register(events.NewMessage(incoming=True, func=TextFilter(source_type=SourceType.USER)))
async def handle_text_message_user_chat(event):
    logger.info(f"New message from USER CHAT")
    client: TelegramClient = event.client
    client_info = await client.get_me()
    # Создаем объект заголовка сообщения
    sender: User = await event.client.get_entity(await event.get_input_sender())

    try:
        outcome_message = OutcomeMessageDTOQueue(
            message=str(event.message.message),
            from_user=str(event.sender_id),
            first_name=str(sender.first_name) if sender.first_name else "Unknown",
            username=sender.username,
            chat=str(event.chat_id),
            media="None",
            voice="None",
            client_telegram_id=str(client_info.id),
        ).json_string()

    except ValidationError as ve:
        logger.error(f"Ошибка при валидации заголовков: {ve}")
        return
    try:
        await publisher.publish_message_to_subject(
            subject_message=NatsQueueMessageDTOSubject(message=outcome_message,
                                                       subject="message.income.new", ))
        logger.info("Сообщение успешно опубликовано в очередь!")
    except Exception as e:
        logger.error(f"Ошибка при публикации сообщения: {e}")
