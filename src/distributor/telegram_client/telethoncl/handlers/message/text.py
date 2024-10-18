import logging
import os

from environs import Env
from faststream.nats import NatsBroker
from loguru import logger
from pydantic import ValidationError
from telethon import events, types, functions, TelegramClient
from telethon.tl.types import Message

from src.distributor.telegram_client.pyro.client.roters.message.models import HeaderUserMessageDTOQueue

env = Env()
env.read_env('.env')


@events.register(events.NewMessage(incoming=True))
async def handle_voice_message(event):
    logger.info(f"New message")
    print()
    client: TelegramClient = event.client
    client_info = await client.get_me()

    # Создаем объект заголовка сообщения
    try:
        outcome_message = HeaderUserMessageDTOQueue(
            from_user=str(event.message.from_user.id),
            user_name=str(event.message.from_user.username) if event.message.from_user.username else "Unknown",
            chat=str(event.message.chat.id),
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
                message=event.message.text,
                subject="message.income.new",
                headers=outcome_message.dict()
            )
            logger.info("Сообщение успешно опубликовано в очередь!")
        except Exception as e:
            logger.error(f"Ошибка при публикации сообщения: {e}")
