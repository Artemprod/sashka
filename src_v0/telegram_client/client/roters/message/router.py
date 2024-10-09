from environs import Env
from faststream.nats import NatsBroker
from loguru import logger
from pydantic import ValidationError
from pyrogram import Client, filters
from pyrogram.types import Message

from src_v0.telegram_client.client.roters.message.models import HeaderUserMessageDTOQueue
from src_v0.telegram_client.client.roters.router import Router

answ_router = Router(name="my_router")



env = Env()
env.read_env('.env')
@answ_router.message(filters.text)
async def message_handler(message: Message, **kwargs):
    # Получение объекта клиента из аргументов
    client: Client = kwargs['client']

    # Создаем объект заголовка сообщения
    try:
        outcome_message = HeaderUserMessageDTOQueue(
            from_user=str(message.from_user.id),
            user_name=str(message.from_user.username) if message.from_user.username else "Unknown",
            chat=str(message.chat.id),
            media=str(message.media.value) if message.media else "None",
            voice=str(message.voice.file_id) if message.voice else "None",
            client_telegram_id=str(client.me.id),
        )
    except ValidationError as ve:
        logger.error(f"Ошибка при валидации заголовков: {ve}")
        return

    #TODO Вынести в паблишер
    #TODO Настроить конфиги сабджекта
    async with NatsBroker(env("NATS_SERVER")) as broker:
    # Открываем контекстный менеджер на брокере
        try:
            await broker.publish(
                message=message.text,
                subject="message.income.new",
                headers=outcome_message.dict()
            )
            logger.info("Сообщение успешно опубликовано в очередь!")
        except Exception as e:
            logger.error(f"Ошибка при публикации сообщения: {e}")
