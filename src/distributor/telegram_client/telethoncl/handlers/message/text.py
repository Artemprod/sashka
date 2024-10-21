import json
import logging
import os

from environs import Env
from faststream.nats import NatsBroker
from loguru import logger
from pydantic import ValidationError
from telethon import events, types, functions, TelegramClient
from telethon.tl.types import Message, PeerUser, User

from src.distributor.telegram_client.pyro.client.roters.message.models import HeaderUserMessageDTOQueue

env = Env()
env.read_env('.env')


@events.register(events.NewMessage(incoming=True))
async def handle_voice_message(event):
    logger.info(f"New message")
    client: TelegramClient = event.client
    client_info = await client.get_me()
    # Создаем объект заголовка сообщения
    s = await event.get_input_sender()
    sender: User = await event.client.get_entity(s)
    try:
        outcome_message = HeaderUserMessageDTOQueue(
            from_user=str(event.sender_id),
            user_name=str(sender.first_name) if sender.first_name else "Unknown",
            chat=str(event.chat_id),
            media="None",
            voice="None",
            client_telegram_id=str(client_info.id),
        )
    except ValidationError as ve:
        logger.error(f"Ошибка при валидации заголовков: {ve}")
        return

    async with NatsBroker(env("NATS_SERVER")) as broker:
        # Открываем контекстный менеджер на брокере
        try:
            await broker.publish(
                message=event.message.message,
                subject="message.income.new",
                headers=outcome_message.dict()
            )
            logger.info("Сообщение успешно опубликовано в очередь!")
        except Exception as e:
            logger.error(f"Ошибка при публикации сообщения: {e}")
